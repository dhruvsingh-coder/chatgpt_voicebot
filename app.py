import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, ClientSettings
import av
import queue
import speech_recognition as sr
from gtts import gTTS
import os
from dotenv import load_dotenv
import google.generativeai as genai

# ----------------------------
# Load Gemini API key
# ----------------------------
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini = genai.GenerativeModel("gemini-2.0-flash")   # ✅ YOUR MODEL

# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="🎙️ Live Gemini Voice Bot")
st.title("🎙️ Live Gemini Voice Bot")

# ----------------------------
# WebRTC Audio Processor
# ----------------------------
class AudioProcessor:
    def __init__(self):
        self.q = queue.Queue()
        self.audio_frames = []

    def recv(self, frame: av.AudioFrame):
        audio = frame.to_ndarray().flatten().tobytes()
        self.q.put(audio)
        self.audio_frames.append(audio)
        return frame

    def get_audio(self):
        return b"".join(self.audio_frames)

# ----------------------------
# Start webrtc streamer
# ----------------------------
ctx = webrtc_streamer(
    key="live",
    mode=WebRtcMode.SENDONLY,
    client_settings=ClientSettings(
        media_stream_constraints={"audio": True, "video": False}
    ),
    audio_processor_factory=AudioProcessor,
)

# ----------------------------
# Process audio when ready
# ----------------------------
if ctx.state.playing:
    st.info("🎙️ Recording... Speak now!")

    if st.button("⏹️ Stop & Transcribe"):
        audio_processor = ctx.audio_processor
        audio_data = audio_processor.get_audio()

        # Save to wav
        with open("output.wav", "wb") as f:
            f.write(audio_data)

        # Use SpeechRecognition to transcribe
        recognizer = sr.Recognizer()
        with sr.AudioFile("output.wav") as source:
            audio = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio)
                st.success(f"🗣️ You said: {text}")

                # Gemini Response
                gemini_response = gemini.generate_content(text)
                answer = gemini_response.text
                st.write("🤖 Gemini says:", answer)

                # TTS
                tts = gTTS(answer)
                tts.save("response.mp3")
                st.audio("response.mp3", format="audio/mp3")

            except Exception as e:
                st.error(f"Transcription error: {e}")
