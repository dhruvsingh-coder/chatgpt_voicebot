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
gemini_model = genai.GenerativeModel("gemini-1.5-flash")  # Updated to latest model

# App UI
st.set_page_config(page_title="🎙️ Gemini Voice Bot", page_icon="🎙️")
st.title("🎙️ Gemini Voice Bot")
st.write("Click the microphone button to record your question (2-10 seconds works best):")

# === Audio Recording ===
audio_bytes = st.audio_recorder("🎤 Speak now", pause_threshold=2.0)

# Text fallback
text_input = st.text_input("Or type your question here:")

# === Process Input ===
question = ""
if audio_bytes:
    recognizer = sr.Recognizer()
    
    # Create a temporary WAV file
    with NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
        temp_audio.write(audio_bytes)
        temp_audio_path = temp_audio.name
    
    try:
        with sr.AudioFile(temp_audio_path) as source:
            audio_data = recognizer.record(source)
            question = recognizer.recognize_google(audio_data)
            st.success(f"🎤 You said: {question}")
    except sr.UnknownValueError:
        st.error("Google Speech Recognition could not understand audio")
    except sr.RequestError as e:
        st.error(f"Could not request results from Google Speech Recognition service; {e}")
    finally:
        # Clean up temporary file
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
