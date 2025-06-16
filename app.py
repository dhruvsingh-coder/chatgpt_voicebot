import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
from gtts import gTTS
import io
import hashlib
from tempfile import NamedTemporaryFile
from audio_recorder_streamlit import audio_recorder
import time

# === Setup ===
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# === Custom CSS for Beautiful UI ===
st.markdown("""
<style>
    /* Main container */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Chat bubbles */
    .user-message {
        background-color: #4a8cff;
        color: white;
        border-radius: 18px 18px 0 18px;
        padding: 12px 16px;
        margin: 8px 0;
        max-width: 80%;
        margin-left: auto;
    }
    
    .bot-message {
        background-color: #ffffff;
        color: #333;
        border-radius: 18px 18px 18px 0;
        padding: 12px 16px;
        margin: 8px 0;
        max-width: 80%;
        margin-right: auto;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Microphone button container */
    .mic-container {
        display: flex;
        justify-content: center;
        margin: 20px 0;
    }
    
    /* Status indicators */
    .status-box {
        background: rgba(255,255,255,0.9);
        border-radius: 10px;
        padding: 12px;
        margin: 10px 0;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# === App Header ===
st.title("🎙️ Gemini Voice Assistant")
st.markdown("""
<div style="text-align: center; margin-bottom: 20px;">
    <p style="color: #666; font-size: 16px;">Hold the microphone button to speak, release to send</p>
</div>
""", unsafe_allow_html=True)

# === Session State ===
if 'convo' not in st.session_state:
    st.session_state.convo = []
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'recording' not in st.session_state:
    st.session_state.recording = False

# === Conversation History ===
for exchange in st.session_state.convo:
    if exchange['role'] == 'user':
        st.markdown(f"""
        <div style="display: flex; justify-content: flex-end;">
            <div class="user-message">
                {exchange['content']}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="display: flex; justify-content: flex-start;">
            <div class="bot-message">
                {exchange['content']}
            </div>
        </div>
        """, unsafe_allow_html=True)
        if exchange.get('audio'):
            st.audio(exchange['audio'], format='audio/mp3')

# === Voice Recording ===
st.markdown('<div class="mic-container">', unsafe_allow_html=True)
audio_bytes = audio_recorder(
    pause_threshold=5.0,
    sample_rate=44100,
    text="",
    recording_color="#ff4b4b",
    neutral_color="#4b8df8",
    icon_name="microphone",
    icon_size="2x",
)
st.markdown('</div>', unsafe_allow_html=True)

# Visual feedback for recording state
if audio_bytes:
    st.session_state.recording = True
else:
    if st.session_state.recording:
        st.session_state.recording = False
        st.rerun()

if st.session_state.recording:
    st.markdown("""
    <div class="status-box">
        <p style="color: #ff4b4b; font-weight: bold;">🎤 Recording... Speak now</p>
    </div>
    """, unsafe_allow_html=True)

# === Audio Processing ===
def process_audio(audio_data):
    """Convert audio to text using Gemini"""
    try:
        with NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name
        
        audio_file = genai.upload_file(tmp_path, mime_type="audio/wav")
        response = model.generate_content(["Transcribe this audio:", audio_file])
        return response.text
    finally:
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)
        if 'audio_file' in locals():
            genai.delete_file(audio_file.name)

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
        # Show recording status
        with st.empty():
            st.markdown("""
            <div class="status-box">
                <p style="color: #4b8df8; font-weight: bold;">🔄 Processing your voice...</p>
            </div>
            """, unsafe_allow_html=True)
            time.sleep(1)
        
        # Transcribe
        user_text = process_audio(audio_bytes)
        if user_text:
            st.session_state.convo.append({'role': 'user', 'content': user_text})
            
            # Get response
            with st.empty():
                st.markdown("""
                <div class="status-box">
                    <p style="color: #4b8df8; font-weight: bold;">💭 Thinking...</p>
                </div>
                """, unsafe_allow_html=True)
                time.sleep(1)
            
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
st.markdown("""
<div style="text-align: center; margin: 20px 0;">
    <p style="color: #666;">Or type your message below</p>
</div>
""", unsafe_allow_html=True)

if prompt := st.chat_input("Type your message here..."):
    st.session_state.convo.append({'role': 'user', 'content': prompt})
    
    with st.empty():
        st.markdown("""
        <div class="status-box">
            <p style="color: #4b8df8; font-weight: bold;">💭 Thinking...</p>
        </div>
        """, unsafe_allow_html=True)
        time.sleep(1)
    
    response = model.generate_content(prompt)
    response_text = response.text
    response_audio = speak(response_text)
    
    st.session_state.convo.append({
        'role': 'assistant',
        'content': response_text,
        'audio': response_audio
    })
    
    st.rerun()
