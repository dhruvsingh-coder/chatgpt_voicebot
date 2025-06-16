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

# Record
audio = mic_recorder(start_prompt="🎙️ Start recording", stop_prompt="⏹️ Stop recording", key="recorder")

if audio:
    st.success("Audio recorded!")
    # Convert base64 to WAV bytes
    audio_bytes = base64.b64decode(audio['audio_data'].split(",")[1])
    # Save to file
    with open("temp_audio.wav", "wb") as f:
        f.write(audio_bytes)

    # Transcribe
    r = sr.Recognizer()
    with sr.AudioFile("temp_audio.wav") as source:
        audio_data = r.record(source)
        try:
            text = r.recognize_google(audio_data)
            st.write("You said:", text)

            if st.button("💬 Generate Response"):
                with st.spinner("Thinking..."):
                    response = gemini.generate_content(text)
                    answer = response.text
                    st.write("🤖 Gemini says:", answer)

                    tts = gTTS(answer)
                    tts.save("response.mp3")
                    st.audio("response.mp3", format="audio/mp3")
        except Exception as e:
            st.error(f"Error: {e}")
