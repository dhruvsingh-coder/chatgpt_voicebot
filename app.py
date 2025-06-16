import streamlit as st
from st_mic_recorder import mic_recorder
import os
import base64
from gtts import gTTS
import tempfile
import google.generativeai as genai
from dotenv import load_dotenv
import speech_recognition as sr

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini = genai.GenerativeModel("gemini-2.0-flash")

st.set_page_config(page_title="🎙️ Gemini Voice Bot (Cloud-Friendly)")
st.title("🎙️ Gemini Voice Bot (Cloud)")

# 1️⃣  Mic Recorder
st.subheader("🎤 Record with your mic")
audio = mic_recorder(start_prompt="Start Recording", stop_prompt="Stop Recording", key='mic')

# 2️⃣  OR File Upload
st.subheader("📁 Or upload a WAV or MP3")
uploaded_file = st.file_uploader("Upload an audio file", type=['wav', 'mp3'])

transcribed_text = ""

# 3️⃣  Process audio input
recognizer = sr.Recognizer()

if audio is not None:
    # decode base64 mic audio to bytes
    audio_bytes = base64.b64decode(audio.split(",")[1])
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
        tmp_file.write(audio_bytes)
        tmp_file.flush()
        audio_file_path = tmp_file.name

    # transcribe
    with sr.AudioFile(audio_file_path) as source:
        recorded_audio = recognizer.record(source)
        try:
            transcribed_text = recognizer.recognize_google(recorded_audio)
        except Exception as e:
            st.error(f"Transcription error: {e}")

elif uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_file.flush()
        audio_file_path = tmp_file.name

    with sr.AudioFile(audio_file_path) as source:
        recorded_audio = recognizer.record(source)
        try:
            transcribed_text = recognizer.recognize_google(recorded_audio)
        except Exception as e:
            st.error(f"Transcription error: {e}")

# 4️⃣  Show transcription and ask Gemini
if transcribed_text:
    st.write("✅ **You said:**", transcribed_text)

    if st.button("✨ Ask Gemini"):
        with st.spinner("Thinking..."):
            response = gemini.generate_content(transcribed_text)
            answer = response.text
            st.write("🤖 **Gemini says:**", answer)

            # Convert to TTS
            tts = gTTS(answer)
            tts_path = "gemini_response.mp3"
            tts.save(tts_path)
            st.audio(tts_path, format="audio/mp3")

