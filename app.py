import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
from gtts import gTTS
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase
import av
import speech_recognition as sr

# Load env
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=gemini_api_key)
gemini_model = genai.GenerativeModel("gemini-2.0-flash")

st.set_page_config(page_title="🎙️ Gemini Voice Bot")
st.title("🎙️ Gemini Voice Bot")

class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.audio_data = []

    def recv_audio(self, frame: av.AudioFrame):
        self.audio_data.append(frame.to_ndarray().tobytes())

    def get_audio_bytes(self):
        return b"".join(self.audio_data)

# Stream mic
ctx = webrtc_streamer(key="speech")

if ctx.audio_receiver:
    if st.button("Process Speech"):
        audio_bytes = ctx.audio_receiver.get_frames().recv().to_ndarray().tobytes()
        # Save to wav
        with open("temp.wav", "wb") as f:
            f.write(audio_bytes)

        r = sr.Recognizer()
        with sr.AudioFile("temp.wav") as source:
            audio = r.record(source)
            question = r.recognize_google(audio)

        st.write(f"You said: {question}")

        response = gemini_model.generate_content(question)
        answer = response.text
        st.write(f"Gemini: {answer}")

        tts = gTTS(answer)
        tts.save("output.mp3")
        st.audio("output.mp3", format="audio/mp3")
