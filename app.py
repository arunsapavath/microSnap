import streamlit as st
from google import genai
from google.genai import types
from twilio.rest import Client
from prompts import SYSTEM_PROMPT

st.set_page_config(
    page_title="MacroSnap",
    page_icon="🥗",
    layout="centered"
)

# Ask for the user's name and WhatsApp number
if "user_name" not in st.session_state:
    st.session_state.user_name = ""

if "whatsapp_number" not in st.session_state:
    st.session_state.whatsapp_number = ""

if not st.session_state.user_name:
    st.title("Welcome to MacroSnap 🥗")

    name = st.text_input("What is your name?")

    if st.button("Continue"):
        if name.strip():
            st.session_state.user_name = name.strip()
            st.rerun()
        else:
            st.warning("Please enter your name.")

    st.stop()


if not st.session_state.whatsapp_number:
    st.title(f"Nice to meet you, {st.session_state.user_name}! 👋")

    whatsapp = st.text_input("Enter your WhatsApp number")

    if st.button("Start Chat"):
        if whatsapp.strip():
            st.session_state.whatsapp_number = whatsapp.strip()
            st.rerun()
        else:
            st.warning("Please enter your WhatsApp number.")

    st.stop()
# Connect to Gemini
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

twilio_client = Client(
    st.secrets["TWILIO_ACCOUNT_SID"],
    st.secrets["TWILIO_AUTH_TOKEN"]
)

# Page title
with st.sidebar:
    st.header("🥗 MacroSnap")
    st.write("Your personal AI nutrition buddy.")

    st.divider()

    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

    st.subheader("What you can do")
    st.write("💬 Ask nutrition questions")
    st.write("📸 Upload a meal photo")
    st.write("🔥 Estimate calories")
    st.write("💪 Check protein")
    st.write("🥑 Check carbs & fat")

    st.divider()

    st.caption("Nutrition estimates are approximate and not medical advice.")

# Create chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
# Ask the user a question or upload a meal photo
user_message = st.chat_input(
    "Ask me about your food or nutrition...",
    accept_file=True,
    file_type=["jpg", "jpeg", "png"]
)

if user_message:
    # Get the text message
    prompt = user_message.text

    # Get uploaded files
    uploaded_files = user_message.files

    # Show user's message
    if prompt:
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })

        with st.chat_message("user"):
            st.write(prompt)
         
         
    # If a photo was uploaded
    if uploaded_files:
        uploaded_file = uploaded_files[0]

        # Read the image
        image_bytes = uploaded_file.getvalue()
        image_type = uploaded_file.type

        # Show the image
        with st.chat_message("user"):
            st.image(image_bytes, caption="Your meal")

        # Send the image to Gemini
        try:
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=[
                    SYSTEM_PROMPT,
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type=image_type
                    ),
                    prompt if prompt else "Analyze this meal and estimate calories, protein, carbohydrates, and fat."
                ]
            )

        except Exception:
            st.error(
                "⚠️ Gemini is temporarily busy. Please try again in a moment."
            )
            st.stop()

    # If only text was entered
    else:
        try:
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=f"{SYSTEM_PROMPT}\n\nUser: {prompt}"
            )

        except Exception:
            st.error(
                "⚠️ Gemini is temporarily busy. Please try again in a moment."
            )
            st.stop()

    # Show Gemini's response
    st.session_state.messages.append({
        "role": "assistant",
        "content": response.text
    })

    with st.chat_message("assistant"):
        st.write(response.text)

        st.divider()

st.divider()

if st.button("📱 Send Summary to WhatsApp"):

    # Build the conversation summary
    summary = f"MacroSnap Summary for {st.session_state.user_name}\n\n"

    for message in st.session_state.messages:
        if message["role"] == "user":
            summary += f"You: {message['content']}\n"
        else:
            summary += f"MacroSnap: {message['content']}\n"

    try:
        # Get the WhatsApp number
        whatsapp_number = str(
            st.session_state.get("whatsapp_number", "")
        ).strip()

        # Make sure a number was provided
        if not whatsapp_number:
            st.error("❌ Please enter your WhatsApp number first.")
            st.stop()

        # Add whatsapp: prefix if it isn't already there
        if not whatsapp_number.startswith("whatsapp:"):
            whatsapp_number = f"whatsapp:{whatsapp_number}"

        # Get the Twilio WhatsApp sender
        whatsapp_from = st.secrets["TWILIO_WHATSAPP_FROM"].strip()

        # Make sure the sender has the correct prefix
        if not whatsapp_from.startswith("whatsapp:"):
            whatsapp_from = f"whatsapp:{whatsapp_from}"

        # Send WhatsApp message
        message = twilio_client.messages.create(
            from_=whatsapp_from,
            to=whatsapp_number,
            body=summary
        )

        st.success("✅ Summary sent to your WhatsApp!")
        st.write(f"Message SID: {message.sid}")

    except Exception as e:
        st.error("❌ Could not send the WhatsApp message.")

        # Display the actual Twilio error
        st.exception(e)
