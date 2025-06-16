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

# === Audio Input Options ===
input_method = st.radio(
    "Choose input method:",
    ("Upload Audio", "Text Input"),
    horizontal=True
)

question = ""

if input_method == "Upload Audio":
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
        except Exception as e:
            st.error(f"Error processing audio: {e}")
        finally:
            if os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)
else:
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

st.warning("Note: Microphone recording is not supported in Streamlit Cloud. Please upload audio files or use text input.")
