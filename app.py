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

# Process audio when new recording is available
if audio_bytes and not st.session_state.processing:
    current_hash = get_audio_hash(audio_bytes)
    
    if current_hash != st.session_state.last_audio_hash:
        st.session_state.processing = True
        st.session_state.last_audio_hash = current_hash
        
        try:
            # Create a unique temp file path
            temp_filename = f"temp_audio_{int(time.time())}.wav"
            
            # Save audio to file
            with open(temp_filename, "wb") as f:
                f.write(audio_bytes)
            
            # Display audio player
            st.audio(audio_bytes, format="audio/wav")
            
            # Transcribe using Gemini's speech-to-text
            with st.spinner("🔊 Processing your voice..."):
                try:
                    audio_file = {"mime_type": "audio/wav", "file_path": temp_filename}
                    response = gemini_model.generate_content(["Transcribe this audio:", audio_file])
                    transcription = response.text
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
                    st.error(f"Error processing with Gemini: {str(e)}")
        except Exception as e:
            st.error(f"Error handling audio file: {str(e)}")
        finally:
            # Clean up temp file
            try:
                if os.path.exists(temp_filename):
                    os.remove(temp_filename)
            except:
                pass
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

# Add some troubleshooting info
st.sidebar.markdown("""
### Troubleshooting:
1. Allow microphone access when prompted
2. Speak clearly into your microphone
3. Hold the button while speaking
4. Release to send your question
""")
