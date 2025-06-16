import streamlit as st
from streamlit_audio_recorder import audio_recorder
import speech_recognition as sr
import io
from gtts import gTTS
from dotenv import load_dotenv
import google.generativeai as genai
import os

# ✅ Load your .env key
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini = genai.GenerativeModel("gemini-1.5-flash")

st.set_page_config(page_title="🎙️ Gemini Voice Bot")
st.title("🎙️ Real-Time Gemini Voice Bot")

# Record audio
audio_bytes = audio_recorder(text="Click to record", pause_threshold=2.0)

if audio_bytes:
    st.audio(audio_bytes, format="audio/wav")
    st.success("Recording received. Transcribing...")

    # Recognize
    recognizer = sr.Recognizer()
    with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
        audio = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio)
            st.write("You said:", text)
            st.session_state.transcribed_text = text
        except Exception as e:
            st.error(f"Could not transcribe: {e}")

if "transcribed_text" in st.session_state:
    if st.button("🎤 Generate Gemini Response"):
        with st.spinner("Gemini is thinking..."):
            try:
                gemini_response = gemini.generate_content(st.session_state.transcribed_text)
                answer = gemini_response.text
                st.write("🤖 Gemini says:", answer)

                # TTS
                tts = gTTS(answer)
                audio_io = io.BytesIO()
                tts.write_to_fp(audio_io)
                audio_io.seek(0)
                st.audio(audio_io, format="audio/mp3")

            except Exception as e:
                st.error(f"Error: {e}")
