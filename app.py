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
st.write("Press and hold to speak, release when done")

# Initialize session state
if 'conversation' not in st.session_state:
    st.session_state.conversation = []
if 'last_audio_hash' not in st.session_state:
    st.session_state.last_audio_hash = None
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'recording_done' not in st.session_state:
    st.session_state.recording_done = False

# Display chat history
for msg in st.session_state.conversation:
    if msg['role'] == 'user':
        st.chat_message("user").write(msg['content'])
    else:
        st.chat_message("assistant").write(msg['content'])
        if 'audio' in msg:
            st.audio(msg['audio'], format='audio/mp3')

def get_audio_hash(audio_bytes):
    return hashlib.md5(audio_bytes).hexdigest()

# Audio recorder
audio_bytes = audio_recorder(
    pause_threshold=3.0,  # Shorter pause threshold for quicker response
    sample_rate=16000,
    text="",
    neutral_color="#1e88e5",
    recording_color="#e53935",
    icon_name="mic",
    icon_size="2x"
)

# Detect when recording is done
if audio_bytes:
    if not st.session_state.recording_done:
        st.session_state.recording_done = True
        st.session_state.new_audio = audio_bytes
elif st.session_state.recording_done:
    st.session_state.recording_done = False
    audio_bytes = st.session_state.new_audio
    del st.session_state.new_audio

# Audio processing
def process_audio(audio_data):
    with NamedTemporaryFile(suffix=".wav") as tmp:
        tmp.write(audio_data)
        audio_file = genai.upload_file(tmp.name, mime_type="audio/wav")
        response = model.generate_content(["Transcribe this audio:", audio_file])
        genai.delete_file(audio_file.name)
        return response.text

def text_to_speech(text):
    audio = io.BytesIO()
    gTTS(text, lang='en').write_to_fp(audio)
    return audio.getvalue()

# Handle new audio automatically
if 'new_audio' in st.session_state and not st.session_state.processing:
    current_hash = get_audio_hash(st.session_state.new_audio)
    
    if current_hash != st.session_state.last_audio_hash:
        st.session_state.processing = True
        st.session_state.last_audio_hash = current_hash
        
        with st.spinner("Processing your question..."):
            try:
                # Show recording
                st.audio(st.session_state.new_audio, format="audio/wav")
                
                # Transcribe
                text = process_audio(st.session_state.new_audio)
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
