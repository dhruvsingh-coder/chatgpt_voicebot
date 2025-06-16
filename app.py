import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
from gtts import gTTS
import io
import speech_recognition as sr
from tempfile import NamedTemporaryFile
import threading

# === Load environment ===
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

# Configure Gemini
genai.configure(api_key=gemini_api_key)
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

# App UI
st.set_page_config(page_title="🎙️ Gemini Voice Bot", page_icon="🎙️")
st.title("🎙️ Gemini Voice Bot")

# Initialize session state
if 'recording' not in st.session_state:
    st.session_state.recording = False
if 'audio_bytes' not in st.session_state:
    st.session_state.audio_bytes = None

# === Audio Recording ===
def record_audio():
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    
    st.session_state.recording = True
    with microphone as source:
        st.info("Recording... Speak now (5 seconds max)")
        audio = recognizer.listen(source, timeout=5)
        st.session_state.audio_bytes = audio.get_wav_data()
        st.session_state.recording = False

# Recording controls
col1, col2 = st.columns(2)
with col1:
    if st.button("🎤 Start Recording") and not st.session_state.recording:
        threading.Thread(target=record_audio).start()

with col2:
    if st.button("⏹️ Stop Recording") and st.session_state.recording:
        st.session_state.recording = False

# Show recording status
if st.session_state.recording:
    st.warning("Recording in progress...")
    
# Process recorded audio
if st.session_state.audio_bytes and not st.session_state.recording:
    recognizer = sr.Recognizer()
    with NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
        temp_audio.write(st.session_state.audio_bytes)
        temp_audio_path = temp_audio.name
    
    try:
        with sr.AudioFile(temp_audio_path) as source:
            audio_data = recognizer.record(source)
            question = recognizer.recognize_google(audio_data)
            st.success(f"🎤 You said: {question}")
            
            # Generate response
            with st.spinner("Generating response..."):
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
                    
    except sr.UnknownValueError:
        st.error("Could not understand audio. Please try again.")
    except sr.RequestError as e:
        st.error(f"Speech recognition service error: {e}")
    finally:
        if os.path.exists(temp_audio_path):
            os.unlink(temp_audio_path)
        st.session_state.audio_bytes = None

# Text fallback
st.write("---")
text_input = st.text_input("Or type your question here:")
if text_input:
    with st.spinner("Generating response..."):
        response = gemini_model.generate_content(text_input)
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
