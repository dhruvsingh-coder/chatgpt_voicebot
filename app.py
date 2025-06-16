import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
import speech_recognition as sr
from gtts import gTTS

# === Load env ===
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=gemini_api_key)
gemini_model = genai.GenerativeModel("gemini-2.0-flash")

# === Speech recognizer ===
recognizer = sr.Recognizer()

st.set_page_config(page_title="🎙️ Gemini Voice Bot")
st.title("🎙️ Gemini Voice Bot")

if st.button("🎤 Record Your Question"):
    with sr.Microphone() as source:
        st.info("Listening... Speak now!")
        audio = recognizer.listen(source)

    try:
        question = recognizer.recognize_google(audio)
        st.write(f"**You said:** {question}")

        # Gemini response
        response = gemini_model.generate_content(question)
        answer = response.text
        st.write(f"**Gemini:** {answer}")

        # === TTS with gTTS ===
        tts = gTTS(answer)
        tts.save("output.mp3")

        # Play in Streamlit
        audio_file = open("output.mp3", "rb")
        audio_bytes = audio_file.read()
        st.audio(audio_bytes, format="audio/mp3")

    except Exception as e:
        st.error(f"Error: {e}")
