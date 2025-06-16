import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
from gtts import gTTS
import io
import hashlib
from tempfile import NamedTemporaryFile
from audio_recorder_streamlit import audio_recorder

# Must be first command
st.set_page_config(page_title="Voice Assistant", page_icon="🎙️")

# === Setup ===
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# === Simple UI ===
st.title("🎙️ Voice Assistant")
st.markdown("""
<style>
    .mic-btn {
        display: flex;
        justify-content: center;
        margin: 20px 0;
    }
    .mic-btn button {
        background: #1e88e5;
        color: white;
        border: none;
        border-radius: 50%;
        width: 80px;
        height: 80px;
        font-size: 24px;
        cursor: pointer;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        transition: all 0.3s;
    }
    .mic-btn button:active {
        transform: scale(0.95);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'conversation' not in st.session_state:
    st.session_state.conversation = []
if 'processing' not in st.session_state:
    st.session_state.processing = False

# Display chat history
for msg in st.session_state.conversation:
    if msg['role'] == 'user':
        st.chat_message("user").write(msg['content'])
    else:
        st.chat_message("assistant").write(msg['content'])
        if 'audio' in msg:
            st.audio(msg['audio'], format='audio/mp3')

# Large microphone button
st.markdown('<div class="mic-btn">', unsafe_allow_html=True)
audio_bytes = audio_recorder(
    pause_threshold=3.0,
    sample_rate=16000,
    text="",
    neutral_color="#1e88e5",
    recording_color="#e53935",
    icon_name="microphone",
    icon_size="3x"
)
st.markdown('</div>', unsafe_allow_html=True)

# Audio processing functions
def process_audio(audio_data):
    with NamedTemporaryFile(suffix=".wav") as tmp:
        tmp.write(audio_data)
        audio_file = genai.upload_file(tmp.name, mime_type="audio/wav")
        response = model.generate_content(["Transcribe:", audio_file])
        genai.delete_file(audio_file.name)
        return response.text

def text_to_speech(text):
    audio = io.BytesIO()
    gTTS(text, lang='en').write_to_fp(audio)
    return audio.getvalue()

# Automatic processing when recording ends
if audio_bytes and not st.session_state.processing:
    st.session_state.processing = True
    
    with st.spinner("Processing your question..."):
        try:
            # Show recording
            st.audio(audio_bytes, format="audio/wav")
            
            # Transcribe
            text = process_audio(audio_bytes)
            st.session_state.conversation.append({'role': 'user', 'content': text})
            
            # Get response
            response = model.generate_content(text)
            response_text = response.text
            response_audio = text_to_speech(response_text)
            
            st.session_state.conversation.append({
                'role': 'assistant', 
                'content': response_text,
                'audio': response_audio
            })
            
        except Exception as e:
            st.error(f"Error: {str(e)}")
        finally:
            st.session_state.processing = False
            st.rerun()

# Text input fallback
if prompt := st.chat_input("Or type your question..."):
    if not st.session_state.processing:
        st.session_state.processing = True
        with st.spinner("Generating response..."):
            try:
                response = model.generate_content(prompt)
                response_text = response.text
                response_audio = text_to_speech(response_text)
                
                st.session_state.conversation.extend([
                    {'role': 'user', 'content': prompt},
                    {'role': 'assistant', 'content': response_text, 'audio': response_audio}
                ])
            except Exception as e:
                st.error(f"Error: {str(e)}")
            finally:
                st.session_state.processing = False
                st.rerun()
