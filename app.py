import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
from gtts import gTTS
import tempfile
import speech_recognition as sr

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini = genai.GenerativeModel("gemini-2.0-flash")

st.set_page_config(page_title="🎙️ Fast Gemini Voice Bot")
st.title("🎙️ Fast Gemini Voice Bot")

# 1️⃣ Record audio using Streamlit's audio recorder
audio_data = st.audio_recorder("Record your voice")

if audio_data is not None:
    # Save recording to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(audio_data)
        tmp_path = tmp.name

    st.success("Recording saved, transcribing...")

    # 2️⃣ Transcribe using SpeechRecognition
    recognizer = sr.Recognizer()
    with sr.AudioFile(tmp_path) as source:
        audio = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio)
            st.write(f"**You said:** {text}")

            # 3️⃣ Get Gemini response
            response = gemini.generate_content(text)
            answer = response.text
            st.write(f"**Gemini:** {answer}")

            # 4️⃣ TTS
            tts = gTTS(answer)
            tts_file = "response.mp3"
            tts.save(tts_file)
            st.audio(tts_file, format="audio/mp3")

        except sr.UnknownValueError:
            st.error("Could not understand audio.")
        except sr.RequestError as e:
            st.error(f"API error: {e}")
