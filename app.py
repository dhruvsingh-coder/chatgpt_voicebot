import os
import io
import wave
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
from gtts import gTTS
import speech_recognition as sr
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode

# === Load .env ===
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

# === Configure Gemini ===
genai.configure(api_key=gemini_api_key)
gemini_model = genai.GenerativeModel("gemini-2.0-flash")

st.set_page_config(page_title="🎙️ Gemini Voice Bot")
st.title("🎙️ Gemini Voice Bot")

st.write("🎤 Click **Start** to record your voice:")

# === Audio Processor ===
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.frames = []

    def recv_audio(self, frame):
        self.frames.append(frame.to_ndarray().tobytes())
        return frame

# === Live mic ===
ctx = webrtc_streamer(
    key="speech",
    mode=WebRtcMode.SENDRECV,  # ✅ CORRECT ENUM!
    audio_receiver_size=1024,
    media_stream_constraints={"video": False, "audio": True},
    audio_processor_factory=AudioProcessor,
    async_processing=True,
)

# === When done ===
if ctx.audio_processor and not ctx.state.playing and ctx.audio_processor.frames:
    st.info("Recording complete. Converting speech to text...")

    wav_io = io.BytesIO()

    with wave.open(wav_io, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)      # 16-bit PCM
        wf.setframerate(48000)  # Default WebRTC mic sample rate
        wf.writeframes(b''.join(ctx.audio_processor.frames))

    wav_io.seek(0)
    st.audio(wav_io, format="audio/wav")

    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_io) as source:
        audio_data = recognizer.record(source)
        try:
            question = recognizer.recognize_google(audio_data)
            st.success(f"**You said:** {question}")

            response = gemini_model.generate_content(question)
            answer = response.text
            st.info(f"**Gemini says:** {answer}")

            tts = gTTS(answer)
            mp3_fp = io.BytesIO()
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)
            st.audio(mp3_fp, format="audio/mp3")

        except Exception as e:
            st.error(f"Error: {e}")
