import os
import io
import wave
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
from gtts import gTTS
import speech_recognition as sr
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode

# === Load .env (for local) ===
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

# === Configure Gemini ===
genai.configure(api_key=gemini_api_key)
gemini_model = genai.GenerativeModel("gemini-2.0-flash")

st.set_page_config(page_title="🎙️ Gemini Voice Bot")
st.title("🎙️ Gemini Voice Bot 🤖🎤")

st.write("Click **Start** to record your voice and get Gemini's answer!")

# === Audio Processor ===
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.frames = []

    def recv_audio(self, frame):
        self.frames.append(frame.to_ndarray().tobytes())
        return frame

# === Mic Recorder ===
ctx = webrtc_streamer(
    key="speech",
    mode=WebRtcMode.SENDRECV,
    audio_receiver_size=1024,
    media_stream_constraints={"video": False, "audio": True},
    audio_processor_factory=AudioProcessor,
    async_processing=True,
)

# === Process after recording ===
if ctx.audio_processor and not ctx.state.playing and ctx.audio_processor.frames:
    st.info("Recording complete! Processing...")

    # Convert frames to WAV
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(48000)  # WebRTC default
        wf.writeframes(b''.join(ctx.audio_processor.frames))

    wav_buffer.seek(0)
    st.audio(wav_buffer, format="audio/wav")

    # === Speech to Text ===
    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_buffer) as source:
        audio_data = recognizer.record(source)
        try:
            question = recognizer.recognize_google(audio_data)
            st.success(f"**You said:** {question}")

            # Gemini response
            response = gemini_model.generate_content(question)
            answer = response.text
            st.info(f"**Gemini says:** {answer}")

            # Text to Speech
            tts = gTTS(answer)
            mp3_io = io.BytesIO()
            tts.write_to_fp(mp3_io)
            mp3_io.seek(0)
            st.audio(mp3_io, format="audio/mp3")

        except Exception as e:
            st.error(f"Error: {e}")
