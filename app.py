import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
from gtts import gTTS
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode
import av
import tempfile
import wave
import numpy as np
import speech_recognition as sr

# Load .env variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-2.0-flash")

st.set_page_config(page_title="🎙️ Gemini Voice Bot")
st.title("🎙️ Gemini Voice Bot")

st.markdown(
    """
    ### 🎤 Speak to the Gemini bot using your mic!
    1. Click **Start**
    2. Click **Stop** when done
    3. Click **Transcribe & Get Answer**
    """
)

class AudioProcessor(AudioProcessorBase):
    def __init__(self) -> None:
        self.frames = []

    def recv_audio(self, frame: av.AudioFrame) -> av.AudioFrame:
        audio = frame.to_ndarray().flatten().astype(np.int16).tobytes()
        self.frames.append(audio)
        return frame

    def get_wav(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            wf = wave.open(f.name, "wb")
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(b''.join(self.frames))
            wf.close()
            return f.name

# Start mic stream
ctx = webrtc_streamer(
    key="speech",
    mode=WebRtcMode.SENDONLY,
    audio_processor_factory=AudioProcessor,
    media_stream_constraints={"audio": True, "video": False},
)

if ctx.state.audio_processor:
    if st.button("Transcribe & Get Answer"):
        audio_file = ctx.state.audio_processor.get_wav()

        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data)
                st.write(f"**You said:** {text}")

                # Gemini API
                response = gemini_model.generate_content(text)
                answer = response.text
                st.write(f"**Gemini:** {answer}")

                # TTS
                tts = gTTS(answer)
                tts_file = "response.mp3"
                tts.save(tts_file)
                st.audio(tts_file, format="audio/mp3")

            except sr.UnknownValueError:
                st.error("Could not understand audio.")
            except sr.RequestError as e:
                st.error(f"API error: {e}")
