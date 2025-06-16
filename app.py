import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
from gtts import gTTS
import io
import base64
import time

# === Load environment ===
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

# Configure Gemini
genai.configure(api_key=gemini_api_key)
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

# App UI
st.set_page_config(page_title="🎙️ Real-time Voice Chat", page_icon="🎙️")
st.title("🎙️ Real-time Voice Chat with Gemini")

# Custom HTML/JS for browser-based recording
recording_js = """
<script>
let mediaRecorder;
let audioChunks = [];

function startRecording() {
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.start();
            
            mediaRecorder.ondataavailable = e => {
                audioChunks.push(e.data);
            };
            
            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                audioChunks = [];
                
                const reader = new FileReader();
                reader.readAsDataURL(audioBlob);
                reader.onloadend = () => {
                    const base64data = reader.result.split(',')[1];
                    window.parent.postMessage({
                        type: 'audioData',
                        data: base64data
                    }, '*');
                };
            };
            
            document.getElementById('status').textContent = "Recording...";
        })
        .catch(err => {
            console.error("Error accessing microphone:", err);
            document.getElementById('status').textContent = "Microphone access denied";
        });
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        document.getElementById('status').textContent = "Processing...";
    }
}
</script>
"""

# Display recording interface
st.components.v1.html(recording_js + """
<div style="text-align: center;">
    <button onclick="startRecording()" style="padding: 10px 20px; margin: 10px;">Start Recording</button>
    <button onclick="stopRecording()" style="padding: 10px 20px; margin: 10px;">Stop Recording</button>
    <p id="status">Ready to record</p>
</div>
""", height=150)

# Audio processing
if 'audio_data' not in st.session_state:
    st.session_state.audio_data = None

# Handle audio data from JS
def handle_audio_data(data):
    st.session_state.audio_data = data
    st.rerun()

# Register callback for JS messages
st.components.v1.html("""
<script>
window.addEventListener('message', (event) => {
    if (event.data.type === 'audioData') {
        window.parent.streamlitApi.sendMessage(event.data);
    }
});
</script>
""", height=0)

# Process audio when received
if st.session_state.audio_data:
    try:
        # Convert base64 to audio file
        audio_bytes = base64.b64decode(st.session_state.audio_data)
        
        # Display audio player
        st.audio(audio_bytes, format='audio/wav')
        
        # Transcribe using Gemini's speech-to-text
        with st.spinner("Transcribing..."):
            audio_file = {"mime_type": "audio/wav", "data": audio_bytes}
            response = gemini_model.generate_content(["Transcribe this audio:", audio_file])
            transcription = response.text
            st.write(f"**You said:** {transcription}")
            
            # Generate response
            with st.spinner("Generating response..."):
                chat_response = gemini_model.generate_content(transcription)
                answer = chat_response.text
                st.write(f"**Gemini:** {answer}")
                
                # Convert response to speech
                with st.spinner("Generating voice..."):
                    tts = gTTS(answer, lang='en')
                    audio_fp = io.BytesIO()
                    tts.write_to_fp(audio_fp)
                    audio_fp.seek(0)
                    st.audio(audio_fp, format='audio/mp3')
                    
    except Exception as e:
        st.error(f"Error processing audio: {str(e)}")
    finally:
        st.session_state.audio_data = None

# Handle JS messages
if st.rerun():
    if 'message' in st.session_state:
        if st.session_state.message.get('type') == 'audioData':
            handle_audio_data(st.session_state.message['data'])
