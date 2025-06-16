import streamlit as st
from streamlit_mic_recorder import mic_recorder
import base64
import speech_recognition as sr
from gtts import gTTS
from dotenv import load_dotenv
import google.generativeai as genai
import os

# Load Gemini key
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini = genai.GenerativeModel("gemini-1.5-flash")

st.set_page_config(page_title="🎙️ Gemini Voice Bot")
st.title("🎙️ Real-Time Gemini Voice Bot")

# 1️⃣ Record audio
audio = mic_recorder(
    start_prompt="🎙️ Start recording",
    stop_prompt="⏹️ Stop recording",
    key="recorder"
)

# 2️⃣ If recorded, decode base64 & save to file
if audio:
    st.success("✅ Audio recorded!")

    # Handle dict or string robustly
    if isinstance(audio, dict):
        audio_data_url = audio["audio_data"]
    else:
        audio_data_url = audio

    audio_bytes = base64.b64decode(audio_data_url.split(",")[1])
    with open("temp_audio.wav", "wb") as f:
        f.write(audio_bytes)

    # 3️⃣ Transcribe
    recognizer = sr.Recognizer()
    with sr.AudioFile("temp_audio.wav") as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data)
            st.write("🗣️ You said:", text)

            if st.button("💬 Generate Response"):
                with st.spinner("🤖 Thinking..."):
                    gemini_response = gemini.generate_content(text)
                    answer = gemini_response.text
                    st.write("🤖 Gemini says:", answer)

                    # TTS output
                    tts = gTTS(answer)
                    tts.save("response.mp3")
                    st.audio("response.mp3", format="audio/mp3")

        except Exception as e:
            st.error(f"Speech Recognition Error: {e}")
