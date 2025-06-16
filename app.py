import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
from gtts import gTTS
import io
import hashlib
from tempfile import NamedTemporaryFile
from audio_recorder_streamlit import audio_recorder

# === Setup ===
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# === App UI ===
st.set_page_config(page_title="🎙️ Gemini Voice Assistant", page_icon="🎙️")
st.title("🎙️ Gemini Voice Assistant")
st.caption("Speak naturally and get intelligent voice responses")

# === Session State ===
if 'convo' not in st.session_state:
    st.session_state.convo = []
if 'processing' not in st.session_state:
    st.session_state.processing = False

# === Conversation History ===
for exchange in st.session_state.convo:
    role = "👤 You" if exchange['role'] == 'user' else "🤖 Gemini"
    st.chat_message(role).write(exchange['content'])
    if exchange.get('audio'):
        st.audio(exchange['audio'], format='audio/mp3')

# === Voice Recording ===
audio_bytes = audio_recorder(
    pause_threshold=8.0,
    sample_rate=44100,
    text="Hold to speak",
    recording_color="#FF0000",
    neutral_color="#00AAFF",
    icon_name="mic",
    icon_size="2x",
)

# === Audio Processing ===
def process_audio(audio_data):
    """Convert audio to text using Gemini"""
    try:
        with NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name
        
        audio_file = genai.upload_file(tmp_path, mime_type="audio/wav")
        response = model.generate_content(["Transcribe this:", audio_file])
        return response.text
    finally:
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)
        if 'audio_file' in locals():
            genai.delete_file(audio_file.name)

# === Text-to-Speech ===
def speak(text):
    """Convert text to speech"""
    tts = gTTS(text, lang='en')
    audio = io.BytesIO()
    tts.write_to_fp(audio)
    return audio.getvalue()

# === Handle New Audio ===
if audio_bytes and not st.session_state.processing:
    st.session_state.processing = True
    
    try:
        # Show recording
        st.audio(audio_bytes, format="audio/wav")
        
        # Transcribe
        with st.spinner("🔄 Processing your voice..."):
            user_text = process_audio(audio_bytes)
            if user_text:
                st.session_state.convo.append({'role': 'user', 'content': user_text})
                
                # Get response
                with st.spinner("💭 Thinking..."):
                    gemini_response = model.generate_content(user_text)
                    response_text = gemini_response.text
                    response_audio = speak(response_text)
                    
                    st.session_state.convo.append({
                        'role': 'assistant',
                        'content': response_text,
                        'audio': response_audio
                    })
                    
                    st.rerun()
    except Exception as e:
        st.error(f"Error: {str(e)}")
    finally:
        st.session_state.processing = False

# === Text Input Fallback ===
if prompt := st.chat_input("Or type your message..."):
    st.session_state.convo.append({'role': 'user', 'content': prompt})
    
    with st.spinner("💭 Thinking..."):
        response = model.generate_content(prompt)
        response_text = response.text
        response_audio = speak(response_text)
        
        st.session_state.convo.append({
            'role': 'assistant',
            'content': response_text,
            'audio': response_audio
        })
        
        st.rerun()
