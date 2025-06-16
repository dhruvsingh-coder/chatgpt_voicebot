import os
import io
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
from gtts import gTTS
import speech_recognition as sr
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase

# Load API key
if "GEMINI_API_KEY" in st.secrets:
    gemini_api_key = st.secrets["GEMINI_API_KEY"]
else:
    load_dotenv()
    gemini_api_key = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=gemini_api_key)
gemini_model = genai.GenerativeModel("gemini-2.0-flash")

st.set_page_config(page_title="🎙️ Gemini Voice Bot")
st.title("🎙️ Gemini Voice Bot")

st.write("🎤 Click Start and speak:")

class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.buffer = b""

    def recv_audio(self, frame):
        self.buffer += frame.to_ndarray().tobytes()
        return frame

ctx = webrtc_streamer(
    key="speech",
    mode="SENDRECV",
    audio_receiver_size=1024,
    media_stream_constraints={"video": False, "audio": True},
    audio_processor_factory=AudioProcessor,
    async_processing=True,
)

if ctx.state.playing:
    st.info("Recording... Speak into your mic.")
elif ctx.audio_processor:
    st.success("Recording finished. Processing...")

    # Save raw audio bytes to WAV for SpeechRecognition
    wav_io = io.BytesIO(ctx.audio_processor.buffer)
    with open("temp.wav", "wb") as f:
        f.write(wav_io.read())

    recognizer = sr.Recognizer()
    with sr.AudioFile("temp.wav") as source:
        audio_data = recognizer.record(source)
        try:
            question = recognizer.recognize_google(audio_data)
            st.write(f"**You said:** {question}")

            response = gemini_model.generate_content(question)
            answer = response.text
            st.write(f"**Gemini:** {answer}")

            tts = gTTS(answer)
            mp3_fp = io.BytesIO()
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)

            st.audio(mp3_fp, format="audio/mp3")

        except Exception as e:
            st.error(f"Error: {e}")
