import os
import av
import io
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
import speech_recognition as sr
from gtts import gTTS
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase

# === Load environment ===
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel("gemini-2.0-flash")

st.set_page_config(page_title="🎙️ Gemini Voice Bot")
st.title("🎙️ Gemini Voice Bot 🤖🎤")

# ✅ FIXED multiline text using triple quotes
st.write("""
1️⃣ Click **Start**  
2️⃣ Speak into mic  
3️⃣ Click **Stop**  
4️⃣ Click **Process & Send to Gemini**  
5️⃣ Hear Gemini's answer!
""")

# === WebRTC audio recorder ===

class AudioProcessor(AudioProcessorBase):
    def __init__(self) -> None:
        self.frames = []

    def recv_audio(self, frame: av.AudioFrame) -> av.AudioFrame:
        self.frames.append(frame.to_ndarray().tobytes())
        return frame

    def get_audio(self):
        return b"".join(self.frames)

ctx = webrtc_streamer(
    key="speech",
    mode="SENDRECV",
    audio_processor_factory=AudioProcessor,
    media_stream_constraints={"audio": True, "video": False},
    async_processing=True,
)

if ctx.state.audio_processor:
    if st.button("🎙️ Process & Send to Gemini"):
        audio_bytes = ctx.state.audio_processor.get_audio()
        
        # Save raw PCM as WAV
        temp_wav = "temp.wav"
        with open(temp_wav, "wb") as f:
            f.write(audio_bytes)

        # Use SpeechRecognition to transcribe
        recognizer = sr.Recognizer()
        with sr.AudioFile(temp_wav) as source:
            audio_data = recognizer.record(source)
            try:
                question = recognizer.recognize_google(audio_data)
                st.success(f"**You said:** {question}")

                response = gemini_model.generate_content(question)
                answer = response.text
                st.info(f"**Gemini says:** {answer}")

                tts = gTTS(answer)
                mp3_io = io.BytesIO()
                tts.write_to_fp(mp3_io)
                mp3_io.seek(0)
                st.audio(mp3_io, format="audio/mp3")

            except Exception as e:
                st.error(f"Error: {e}")
