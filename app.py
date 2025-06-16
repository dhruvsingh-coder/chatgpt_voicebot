import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
from gtts import gTTS
import io
import base64
import time
from audio_recorder_streamlit import audio_recorder

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
if 'last_audio' not in st.session_state:
    st.session_state.last_audio = None

# Audio recorder component
st.write("Click the microphone to record your question (5 seconds max):")
audio_bytes = audio_recorder(pause_threshold=5.0, sample_rate=44100)

# Process audio when new recording is available
if audio_bytes and audio_bytes != st.session_state.last_audio and not st.session_state.processing:
    st.session_state.processing = True
    st.session_state.last_audio = audio_bytes
    
    try:
        # Display audio player
        st.audio(audio_bytes, format="audio/wav")
        
        # Save to temporary file
        with open("temp_audio.wav", "wb") as f:
            f.write(audio_bytes)
        
        # Transcribe using Gemini's speech-to-text
        with st.spinner("🔊 Transcribing your voice..."):
            audio_file = {"mime_type": "audio/wav", "file_path": "temp_audio.wav"}
            response = gemini_model.generate_content(["Transcribe this audio:", audio_file])
            transcription = response.text
            st.write(f"**You said:** {transcription}")
            
            # Generate response
            with st.spinner("🧠 Generating response..."):
                chat_response = gemini_model.generate_content(transcription)
                answer = chat_response.text
                st.write(f"**Gemini:** {answer}")
                
                # Convert response to speech
                with st.spinner("🗣️ Generating voice response..."):
                    tts = gTTS(answer, lang='en')
                    audio_fp = io.BytesIO()
                    tts.write_to_fp(audio_fp)
                    audio_fp.seek(0)
                    st.audio(audio_fp, format='audio/mp3')
                    
    except Exception as e:
        st.error(f"Error processing audio: {str(e)}")
    finally:
        if os.path.exists("temp_audio.wav"):
            os.remove("temp_audio.wav")
        st.session_state.processing = False
        st.rerun()

# Text fallback
st.write("---")
text_input = st.text_input("Or type your question here:")
if text_input and not st.session_state.processing:
    with st.spinner("🧠 Generating response..."):
        response = gemini_model.generate_content(text_input)
        answer = response.text
        
        st.write(f"**You asked:** {text_input}")
        st.write(f"**Gemini:** {answer}")
        
        with st.spinner("🗣️ Generating voice response..."):
            tts = gTTS(answer, lang='en')
            audio_fp = io.BytesIO()
            tts.write_to_fp(audio_fp)
            audio_fp.seek(0)
            st.audio(audio_fp, format='audio/mp3')
