import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
from gtts import gTTS
import io
import time
from audio_recorder_streamlit import audio_recorder
import hashlib

# === Load environment ===
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

# Configure Gemini
genai.configure(api_key=gemini_api_key)
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

# App UI
st.set_page_config(page_title="🎙️ Real-time Voice Chat", page_icon="🎙️")
st.title("🎙️ Real-time Voice Chat with Gemini")

# Initialize session state
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'last_audio_hash' not in st.session_state:
    st.session_state.last_audio_hash = None

def get_audio_hash(audio_bytes):
    return hashlib.md5(audio_bytes).hexdigest()

# Audio recorder component
st.write("Press and hold to record your question (max 10 seconds):")
audio_bytes = audio_recorder(
    pause_threshold=10.0,
    sample_rate=44100,
    text="Hold to Talk",
    recording_color="#e8b62c",
    neutral_color="#6aa36f",
    icon_name="microphone",
    icon_size="2x",
)

def process_audio_with_gemini(audio_bytes):
    """Process audio bytes with Gemini's speech-to-text"""
    try:
        # Create a temporary file
        with NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            temp_audio.write(audio_bytes)
            temp_path = temp_audio.name
        
        # Create the proper audio input format for Gemini
        audio_file = genai.upload_file(path=temp_path, mime_type="audio/wav")
        
        # Generate content with the audio file
        response = gemini_model.generate_content(
            ["Transcribe this audio:", audio_file]
        )
        return response.text
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        # Delete the uploaded file from Gemini's servers
        if 'audio_file' in locals():
            genai.delete_file(audio_file.name)

# Process audio when new recording is available
if audio_bytes and not st.session_state.processing:
    current_hash = get_audio_hash(audio_bytes)
    
    if current_hash != st.session_state.last_audio_hash:
        st.session_state.processing = True
        st.session_state.last_audio_hash = current_hash
        
        try:
            # Display audio player
            st.audio(audio_bytes, format="audio/wav")
            
            # Transcribe using Gemini's speech-to-text
            with st.spinner("🔊 Processing your voice..."):
                transcription = process_audio_with_gemini(audio_bytes)
                st.write(f"**You said:** {transcription}")
                
                # Generate response
                with st.spinner("🧠 Thinking..."):
                    chat_response = gemini_model.generate_content(transcription)
                    answer = chat_response.text
                    st.write(f"**Gemini:** {answer}")
                    
                    # Convert response to speech
                    with st.spinner("🗣️ Preparing voice response..."):
                        tts = gTTS(answer, lang='en')
                        audio_fp = io.BytesIO()
                        tts.write_to_fp(audio_fp)
                        audio_fp.seek(0)
                        st.audio(audio_fp, format='audio/mp3')
        except Exception as e:
            st.error(f"Error processing: {str(e)}")
        finally:
            st.session_state.processing = False

# Text fallback
st.write("---")
st.write("Alternatively, type your question below:")
text_input = st.text_input("Text input")
if text_input and not st.session_state.processing:
    with st.spinner("🧠 Thinking..."):
        response = gemini_model.generate_content(text_input)
        answer = response.text
        
        st.write(f"**You asked:** {text_input}")
        st.write(f"**Gemini:** {answer}")
        
        with st.spinner("🗣️ Preparing voice response..."):
            tts = gTTS(answer, lang='en')
            audio_fp = io.BytesIO()
            tts.write_to_fp(audio_fp)
            audio_fp.seek(0)
            st.audio(audio_fp, format='audio/mp3')
