import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
from gtts import gTTS
import io
from streamlit_audio_recorder import audio_recorder
import speech_recognition as sr

# === Load environment ===
# On Streamlit Cloud, use st.secrets instead of .env
if "GEMINI_API_KEY" in st.secrets:
    gemini_api_key = st.secrets["GEMINI_API_KEY"]
else:
    load_dotenv()
    gemini_api_key = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=gemini_api_key)
gemini_model = genai.GenerativeModel("gemini-2.0-flash")

st.set_page_config(page_title="🎙️ Gemini Voice Bot")
st.title("🎙️ Gemini Voice Bot")

st.write("🎤 Click the button to record your voice question using your browser mic.")

# === Use streamlit-audio-recorder ===
audio_bytes = audio_recorder(
    text="Click to record",
    recording_color="#e30022",
    neutral_color="#6aa36f",
    icon_name="microphone",
    icon_size="6x",
)

if audio_bytes:
    st.audio(audio_bytes, format="audio/wav")
    st.info("Transcribing your audio...")

    # Save in-memory for SpeechRecognition
    with open("temp_recording.wav", "wb") as f:
        f.write(audio_bytes)

    recognizer = sr.Recognizer()
    with sr.AudioFile("temp_recording.wav") as source:
        audio_data = recognizer.record(source)
        try:
            question = recognizer.recognize_google(audio_data)
            st.write(f"**You said:** {question}")

            # Gemini response
            response = gemini_model.generate_content(question)
            answer = response.text
            st.write(f"**Gemini:** {answer}")

            # TTS in-memory
            tts = gTTS(answer)
            mp3_fp = io.BytesIO()
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)

            st.audio(mp3_fp, format="audio/mp3")

        except Exception as e:
            st.error(f"Could not process audio: {e}")
