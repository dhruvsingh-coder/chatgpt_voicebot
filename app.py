import streamlit as st
from streamlit_mic_recorder import mic_recorder
import os
import speech_recognition as sr
from gtts import gTTS
from dotenv import load_dotenv
import google.generativeai as genai

# Load API key
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini = genai.GenerativeModel("gemini-1.5-flash")

st.set_page_config(page_title="🎙️ Gemini Voice Bot")
st.title("🎙️ Real-Time Gemini Voice Bot")

# Record audio
audio = mic_recorder(start_prompt="Start recording", stop_prompt="Stop recording", key="recorder")

if audio:
    # Save to file
    audio_file = "input.wav"
    with open(audio_file, "wb") as f:
        f.write(audio)

    # Transcribe
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data)
            st.write("✅ **You said:**", text)

            if st.button("🔮 Generate Response"):
                gemini_response = gemini.generate_content(text)
                answer = gemini_response.text
                st.write("🤖 **Gemini says:**", answer)

                tts = gTTS(answer)
                tts_path = "response.mp3"
                tts.save(tts_path)
                st.audio(tts_path, format="audio/mp3")

        except Exception as e:
            st.error(f"Error: {e}")
