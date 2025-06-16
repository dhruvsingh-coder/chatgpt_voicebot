import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
from gtts import gTTS
import io

# === Load environment ===
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=gemini_api_key)
gemini_model = genai.GenerativeModel("gemini-2.0-flash")

st.set_page_config(page_title="🎙️ Gemini Voice Bot")
st.title("🎙️ Gemini Voice Bot")

st.write(
    "Upload an audio file (WAV/MP3) or record below (using Streamlit's recording widget if available)."
)

# === Upload audio ===
audio_file = st.file_uploader("Upload your question (wav/mp3):", type=["wav", "mp3"])

# === Optional: Text input as fallback ===
text_input = st.text_input("Or type your question here:")

# === Process audio ===
import speech_recognition as sr

if audio_file is not None:
    recognizer = sr.Recognizer()
    with open("temp_audio.wav", "wb") as f:
        f.write(audio_file.read())

    with sr.AudioFile("temp_audio.wav") as source:
        audio_data = recognizer.record(source)
        try:
            question = recognizer.recognize_google(audio_data)
            st.write(f"**You said:** {question}")
        except Exception as e:
            st.error(f"Could not process audio: {e}")
            question = ""

elif text_input:
    question = text_input
else:
    question = ""

# === Generate answer ===
if question:
    response = gemini_model.generate_content(question)
    answer = response.text
    st.write(f"**Gemini:** {answer}")

    # === Text-to-Speech ===
    tts = gTTS(answer)
    mp3_fp = io.BytesIO()
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)

    st.audio(mp3_fp, format="audio/mp3")

