import os
import io
import wave
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
from gtts import gTTS
import speech_recognition as sr
import st_audiorec

# === Load env ===
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel("gemini-2.0-flash")

st.set_page_config(page_title="🎙️ Gemini Voice Bot")
st.title("🎙️ Gemini Voice Bot 🤖🎤")

st.write("Click **Start Recording**, then **Stop**, then **Submit** to get Gemini's answer!")

# === Use st_audiorec ===
audio_bytes = st_audiorec.st_audiorec()

if audio_bytes:
    st.audio(audio_bytes, format="audio/wav")
    st.info("Processing your recording...")

    # === Speech to Text ===
    recognizer = sr.Recognizer()
    wav_io = io.BytesIO(audio_bytes)
    with sr.AudioFile(wav_io) as source:
        audio_data = recognizer.record(source)
        try:
            question = recognizer.recognize_google(audio_data)
            st.success(f"**You said:** {question}")

            # === Gemini Answer ===
            response = gemini_model.generate_content(question)
            answer = response.text
            st.info(f"**Gemini says:** {answer}")

            # === Text to Speech ===
            tts = gTTS(answer)
            mp3_io = io.BytesIO()
            tts.write_to_fp(mp3_io)
            mp3_io.seek(0)
            st.audio(mp3_io, format="audio/mp3")

        except Exception as e:
            st.error(f"Error: {e}")
