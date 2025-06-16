import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
from gtts import gTTS
import io
import time
from audio_recorder_streamlit import audio_recorder
import hashlib
from tempfile import NamedTemporaryFile

# === Load environment ===
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

# Configure Gemini
genai.configure(api_key=gemini_api_key)
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

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

# App UI
st.set_page_config(page_title="🎙️ Real-time Voice Chat", page_icon="🎙️")
st.title("🎙️ Real-time Voice Chat with Gemini")
st.markdown("""
<div style="text-align: center; margin-bottom: 20px;">
    <p style="color: #666; font-size: 16px;">Hold the microphone button to speak, release to send</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'last_audio_hash' not in st.session_state:
    st.session_state.last_audio_hash = None
if 'conversation' not in st.session_state:
    st.session_state.conversation = []

def get_audio_hash(audio_bytes):
    return hashlib.md5(audio_bytes).hexdigest()

# Display conversation history
for exchange in st.session_state.conversation:
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

# Audio recorder component
st.markdown('<div class="mic-container">', unsafe_allow_html=True)
audio_bytes = audio_recorder(
    pause_threshold=10.0,
    sample_rate=44100,
    text="Hold to Talk",
    recording_color="#ff4b4b",
    neutral_color="#4b8df8",
    icon_name="microphone",
    icon_size="2x",
)
st.markdown('</div>', unsafe_allow_html=True)

def process_audio_with_gemini(audio_bytes):
    """Process audio bytes with Gemini's speech-to-text"""
    try:
        # Create a temporary file
        with NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            temp_audio.write(audio_bytes)
            temp_path = temp_audio.name
        
        # Upload the file to Gemini
        audio_file = genai.upload_file(path=temp_path, mime_type="audio/wav")
        
        # Generate content with the audio file
        response = gemini_model.generate_content(
            ["Transcribe this audio:", audio_file]
        )
        return response.text
    except Exception as e:
        st.error(f"Error in audio processing: {str(e)}")
        return None
    finally:
        # Clean up the temporary file
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)
        # Delete the uploaded file from Gemini's servers
        if 'audio_file' in locals():
            try:
                genai.delete_file(audio_file.name)
            except:
                pass

def text_to_speech(text):
    """Convert text to speech audio"""
    tts = gTTS(text, lang='en')
    audio_fp = io.BytesIO()
    tts.write_to_fp(audio_fp)
    audio_fp.seek(0)
    return audio_fp.read()

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
                
                if transcription:
                    st.session_state.conversation.append({
                        'role': 'user',
                        'content': transcription
                    })
                    
                    # Generate response
                    with st.spinner("🧠 Thinking..."):
                        chat_response = gemini_model.generate_content(transcription)
                        answer = chat_response.text
                        
                        # Convert response to speech
                        with st.spinner("🗣️ Preparing voice response..."):
                            audio_response = text_to_speech(answer)
                            
                            st.session_state.conversation.append({
                                'role': 'assistant',
                                'content': answer,
                                'audio': audio_response
                            })
                            
                            # Rerun to update the conversation display
                            st.rerun()
        except Exception as e:
            st.error(f"Error in conversation: {str(e)}")
        finally:
            st.session_state.processing = False

# Text fallback
st.markdown("""
<div style="text-align: center; margin: 20px 0;">
    <p style="color: #666;">Or type your message below</p>
</div>
""", unsafe_allow_html=True)

if prompt := st.chat_input("Type your message here..."):
    st.session_state.processing = True
    
    try:
        st.session_state.conversation.append({
            'role': 'user',
            'content': prompt
        })
        
        with st.spinner("🧠 Thinking..."):
            response = gemini_model.generate_content(prompt)
            answer = response.text
            
            with st.spinner("🗣️ Preparing voice response..."):
                audio_response = text_to_speech(answer)
                
                st.session_state.conversation.append({
                    'role': 'assistant',
                    'content': answer,
                    'audio': audio_response
                })
                
                # Rerun to update the conversation display
                st.rerun()
    except Exception as e:
        st.error(f"Error processing text input: {str(e)}")
    finally:
        st.session_state.processing = False
