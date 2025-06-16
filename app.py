import os
import base64
import streamlit as st
import speech_recognition as sr
from gtts import gTTS
from dotenv import load_dotenv
import google.generativeai as genai

# ----------------------------
# Load Gemini API key
# ----------------------------
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini = genai.GenerativeModel("gemini-1.5-flash")

# ----------------------------
# Streamlit UI Config
# ----------------------------
st.set_page_config(page_title="🎙️ Gemini Voice Bot")
st.title("🎙️ Gemini Voice Bot (Stable Upload Version)")

# ----------------------------
# Record with native browser recorder
# ----------------------------
st.write("🎤 Record your voice using your computer's recorder and upload the file below (WAV or MP3 recommended).")

audio_file = st.file_uploader("Upload your recorded voice here:", type=["wav", "mp3", "m4a"])

if audio_file is not None:
    # Save uploaded audio to disk
    audio_path = f"uploaded_audio.{audio_file.type.split('/')[-1]}"
    with open(audio_path, "wb") as f:
        f.write(audio_file.read())
    st.audio(audio_path)

    # ----------------------------
    # Transcribe
    # ----------------------------
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data)
            st.success(f"🗣️ You said: {text}")
        except Exception as e:
            st.error(f"❌ Speech Recognition Error: {e}")
            st.stop()

    # ----------------------------
    # Generate Gemini response
    # ----------------------------
    if st.button("🤖 Generate Gemini Response"):
        with st.spinner("Thinking..."):
            gemini_response = gemini.generate_content(text)
            answer = gemini_response.text
            st.write("🤖 Gemini says:", answer)

            # TTS output
            tts = gTTS(answer)
            tts.save("response.mp3")
            st.audio("response.mp3", format="audio/mp3")
