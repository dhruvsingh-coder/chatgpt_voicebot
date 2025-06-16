import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
from gtts import gTTS
import io
import speech_recognition as sr
from tempfile import NamedTemporaryFile

# === Load environment ===
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

# Configure Gemini
genai.configure(api_key=gemini_api_key)
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

# App UI
st.set_page_config(page_title="🎙️ Gemini Voice Bot", page_icon="🎙️")
st.title("🎙️ Gemini Voice Bot")

# === Audio Recording Options ===
recording_option = st.radio(
    "Choose input method:",
    ("Use Microphone (Browser)", "Upload Audio File", "Text Input"),
    horizontal=True
)

# === Process Different Input Types ===
question = ""

if recording_option == "Use Microphone (Browser)":
    try:
        from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
        import av
        
        st.warning("Note: Microphone access might require permissions. If it fails, try another method.")
        
        class AudioRecorder(AudioProcessorBase):
            def __init__(self):
                self.audio_bytes = bytearray()

            def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
                self.audio_bytes.extend(frame.to_ndarray().tobytes())
                return frame

        webrtc_ctx = webrtc_streamer(
            key="speech-to-text",
            mode=WebRtcMode.SENDONLY,
            audio_processor_factory=AudioRecorder,
            rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
            media_stream_constraints={"audio": True},
        )

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
                    st.error("Could not understand audio. Please try again.")
                except sr.RequestError as e:
                    st.error(f"Speech recognition service error: {e}")
                finally:
                    if os.path.exists(temp_audio_path):
                        os.unlink(temp_audio_path)

    except Exception as e:
        st.error(f"Microphone access failed: {str(e)}")
        st.info("Please try the upload or text input options below.")

elif recording_option == "Upload Audio File":
    audio_file = st.file_uploader("Upload audio file (WAV/MP3):", type=["wav", "mp3"])
    if audio_file:
        recognizer = sr.Recognizer()
        with NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            temp_audio.write(audio_file.read())
            temp_audio_path = temp_audio.name
        
        try:
            with sr.AudioFile(temp_audio_path) as source:
                audio_data = recognizer.record(source)
                question = recognizer.recognize_google(audio_data)
                st.success(f"🎤 You said: {question}")
        except sr.UnknownValueError:
            st.error("Could not understand audio. Please try a clearer recording.")
        except sr.RequestError as e:
            st.error(f"Speech recognition service error: {e}")
        finally:
            if os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)

else:  # Text Input
    question = st.text_input("Enter your question:")

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
