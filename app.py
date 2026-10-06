import streamlit as st
from google import genai
from google.genai import types
from prompts import SYSTEM_PROMPT

st.set_page_config(
    page_title="MacroSnap",
    page_icon="🥗",
    layout="centered"
)

# Ask for the user's name 
if "user_name" not in st.session_state:
    st.session_state.user_name = ""


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


# Connect to Gemini
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])


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

    
        