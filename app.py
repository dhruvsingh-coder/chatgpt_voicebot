import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
from gtts import gTTS
import io
import speech_recognition as sr
from tempfile import NamedTemporaryFile
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import av

# === Load environment ===
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

# Configure Gemini (using 1.5 Flash - the current equivalent of 2.0 Flash)
genai.configure(api_key=gemini_api_key)
gemini_model = genai.GenerativeModel("gemini-1.5-flash")  # Updated model name

# App UI
st.set_page_config(page_title="🎙️ Gemini Voice Bot", page_icon="🎙️")
st.title("🎙️ Gemini Voice Bot")
st.write("Click 'Start' to record your question (speak clearly for 2-10 seconds), then 'Stop' when done:")

class AudioRecorder(AudioProcessorBase):
    def __init__(self):
        self.audio_bytes = bytearray()

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        self.audio_bytes.extend(frame.to_ndarray().tobytes())
        return frame

# === Audio Recording ===
webrtc_ctx = webrtc_streamer(
    key="speech-to-text",
    mode=WebRtcMode.SENDONLY,
    audio_processor_factory=AudioRecorder,
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    media_stream_constraints={"audio": True},
)

# Text fallback
text_input = st.text_input("Or type your question here:")

# === Process Input ===
question = ""
if webrtc_ctx and webrtc_ctx.audio_processor:
    recognizer = sr.Recognizer()
    audio_bytes = bytes(webrtc_ctx.audio_processor.audio_bytes)
    
    if len(audio_bytes) > 0:
        with NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            temp_audio.write(audio_bytes)
            temp_audio_path = temp_audio.name
        
        try:
            with sr.AudioFile(temp_audio_path) as source:
                audio_data = recognizer.record(source)
                question = recognizer.recognize_google(audio_data)
                st.success(f"🎤 You said: {question}")
        except sr.UnknownValueError:
            st.error("Could not understand audio. Please try again or use text input.")
        except sr.RequestError as e:
            st.error(f"Speech recognition service error: {e}")
        finally:
            if os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)

elif text_input:
    question = text_input

# === Generate and Speak Response ===
if question:
    with st.spinner("Generating response..."):
        try:
            response = gemini_model.generate_content(question)
            answer = response.text
            
            st.subheader("🤖 Gemini Response:")
            st.write(answer)
            
            # Text-to-Speech
            with st.spinner("Generating audio..."):
                tts = gTTS(answer, lang='en')
                audio_fp = io.BytesIO()
                tts.write_to_fp(audio_fp)
                audio_fp.seek(0)
                
                st.audio(audio_fp, format="audio/mp3")
                
        except Exception as e:
            st.error(f"Error generating response: {e}")
