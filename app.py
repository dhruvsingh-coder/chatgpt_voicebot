import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
from gtts import gTTS
import io
import hashlib
from audio_recorder_streamlit import audio_recorder
from tempfile import NamedTemporaryFile

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
if 'conversation' not in st.session_state:
    st.session_state.conversation = []
if 'last_audio_hash' not in st.session_state:
    st.session_state.last_audio_hash = None

# Show conversation history
for exchange in st.session_state.conversation:
    if exchange['role'] == 'user':
        st.write(f"👤 **You:** {exchange['content']}")
    else:
        st.write(f"🤖 **Gemini:** {exchange['content']}")
        if 'audio' in exchange:
            st.audio(exchange['audio'], format='audio/mp3')

st.write("---")

def get_audio_hash(audio_bytes):
    return hashlib.md5(audio_bytes).hexdigest()

def process_audio(audio_bytes):
    """ Process audio using Gemini STT (or Whisper) """
    with NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
        tmpfile.write(audio_bytes)
        tmp_path = tmpfile.name

    try:
        audio_file = genai.upload_file(path=tmp_path, mime_type="audio/wav")
        response = gemini_model.generate_content(
            ["Transcribe this audio:", audio_file]
        )
        return response.text
    finally:
        os.remove(tmp_path)
        try:
            genai.delete_file(audio_file.name)
        except:
            pass

def text_to_speech(text):
    tts = gTTS(text, lang='en')
    audio_fp = io.BytesIO()
    tts.write_to_fp(audio_fp)
    audio_fp.seek(0)
    return audio_fp.read()

# --- Always show recorder ---
st.subheader("🎤 Speak your next question")
audio_bytes = audio_recorder(
    pause_threshold=10.0,
    sample_rate=44100,
    text="Hold to Talk",
    recording_color="#e8b62c",
    neutral_color="#6aa36f",
    icon_name="microphone",
    icon_size="2x",
)

# --- If new audio recorded ---
if audio_bytes:
    current_hash = get_audio_hash(audio_bytes)
    if current_hash != st.session_state.last_audio_hash:
        st.session_state.last_audio_hash = current_hash

        # Play back the recorded audio
        st.audio(audio_bytes, format="audio/wav")

        with st.spinner("🔊 Transcribing..."):
            transcription = process_audio(audio_bytes)

        st.session_state.conversation.append({
            'role': 'user',
            'content': transcription
        })

        with st.spinner("🧠 Thinking..."):
            response = gemini_model.generate_content(transcription)
            answer = response.text

        with st.spinner("🗣️ Preparing voice response..."):
            audio_response = text_to_speech(answer)

        st.session_state.conversation.append({
            'role': 'assistant',
            'content': answer,
            'audio': audio_response
        })

        # Rerun so new history appears & recorder stays visible
        st.experimental_rerun()

# --- Text fallback ---
st.write("---")
st.write("💬 Or type your question:")
text_input = st.text_input("Text input")
if text_input:
    st.session_state.conversation.append({
        'role': 'user',
        'content': text_input
    })

    with st.spinner("🧠 Thinking..."):
        response = gemini_model.generate_content(text_input)
        answer = response.text

    with st.spinner("🗣️ Preparing voice response..."):
        audio_response = text_to_speech(answer)

    st.session_state.conversation.append({
        'role': 'assistant',
        'content': answer,
        'audio': audio_response
    })

    st.experimental_rerun()
