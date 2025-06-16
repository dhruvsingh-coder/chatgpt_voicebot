import os
import io
import wave
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
from gtts import gTTS
import speech_recognition as sr
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase

# Load env
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=gemini_api_key)
gemini_model = genai.GenerativeModel("gemini-2.0-flash")

st.set_page_config(page_title="🎙️ Gemini Voice Bot")
st.title("🎙️ Gemini Voice Bot")

st.write("🎤 Click Start and speak:")

# === Audio processor ===
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.frames = []

    def recv_audio(self, frame):
        self.frames.append(frame.to_ndarray().tobytes())
        return frame

ctx = webrtc_streamer(
    key="speech",
    mode="SENDRECV",
    audio_receiver_size=1024,
    media_stream_constraints={"video": False, "audio": True},
    audio_processor_factory=AudioProcessor,
    async_processing=True,
)

# === After recording ===
if ctx.audio_processor and not ctx.state.playing and ctx.audio_processor.frames:
    st.info("Recording complete. Processing audio...")

    wav_io = io.BytesIO()

    # === Write proper WAV headers ===
    with wave.open(wav_io, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit PCM = 2 bytes
        wf.setframerate(48000)  # Default WebRTC sample rate
        wf.writeframes(b''.join(ctx.audio_processor.frames))

    wav_io.seek(0)
    st.audio(wav_io, format="audio/wav")

    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_io) as source:
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
