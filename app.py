import streamlit as st
from streamlit_webrtc import webrtc_streamer
import av
import os
import tempfile
import speech_recognition as sr
from gtts import gTTS
from dotenv import load_dotenv
import google.generativeai as genai

# Load Gemini key
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini = genai.GenerativeModel("gemini-1.5-flash")

st.set_page_config(page_title="🎙️ Gemini Voice Bot")
st.title("🎙️ Real-Time Gemini Voice Bot")

# Recorder class
class AudioProcessor:
    def __init__(self):
        self.recognizer = sr.Recognizer()

    def recv(self, frame: av.AudioFrame):
        wav_path = "/tmp/audio.wav"
        with open(wav_path, "wb") as f:
            f.write(frame.to_ndarray().tobytes())

        try:
            with sr.AudioFile(wav_path) as source:
                audio = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio)
                st.session_state.transcribed_text = text
        except Exception as e:
            st.session_state.transcribed_text = f"[Error] {str(e)}"

# Start recording
webrtc_ctx = webrtc_streamer(key="example", audio_processor_factory=AudioProcessor, media_stream_constraints={"audio": True, "video": False})

if "transcribed_text" in st.session_state:
    st.write("You said:", st.session_state.transcribed_text)

    if st.button("🎤 Generate Response"):
        with st.spinner("Thinking..."):
            gemini_response = gemini.generate_content(st.session_state.transcribed_text)
            answer = gemini_response.text
            st.write("🤖 Gemini says:", answer)

            # TTS
            tts = gTTS(answer)
            tts_path = "response.mp3"
            tts.save(tts_path)
            st.audio(tts_path, format="audio/mp3")
