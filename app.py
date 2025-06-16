import os
import base64
import streamlit as st
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr
from gtts import gTTS
from dotenv import load_dotenv
import google.generativeai as genai

# ----------------------------
# Load Gemini API key
# ----------------------------
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini = genai.GenerativeModel("gemini-1.5-flash")

# ----------------------------
# Streamlit UI Config
# ----------------------------
st.set_page_config(page_title="🎙️ Gemini Voice Bot")
st.title("🎙️ Real-Time Gemini Voice Bot")

# ----------------------------
# Record audio
# ----------------------------
audio = mic_recorder(
    start_prompt="🎙️ Start recording",
    stop_prompt="⏹️ Stop recording",
    key="recorder"
)

# Debug: show raw mic_recorder output
st.write("DEBUG ➜ Raw audio output:", audio)

# ----------------------------
# If audio exists, process it
# ----------------------------
if audio:
    st.success("✅ Audio recorded!")

    # Safely handle possible keys
    audio_data_url = None
    if isinstance(audio, dict):
        # Print keys to know what's inside
        st.write("DEBUG ➜ Audio keys:", list(audio.keys()))
        # Common candidates: 'audio_data', 'data', 'blob'
        for candidate in ["audio_data", "data", "blob"]:
            if candidate in audio:
                audio_data_url = audio[candidate]
                break
    elif isinstance(audio, str):
        audio_data_url = audio

    # If still none, show error
    if audio_data_url is None:
        st.error("❌ Could not find base64 audio data. Check recorder output.")
        st.stop()

    # Decode base64 and save to wav
    try:
        audio_bytes = base64.b64decode(audio_data_url.split(",")[1])
    except Exception as e:
        st.error(f"❌ Error decoding audio: {e}")
        st.stop()

    wav_path = "temp_audio.wav"
    with open(wav_path, "wb") as f:
        f.write(audio_bytes)

    # ----------------------------
    # Transcribe audio
    # ----------------------------
    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_path) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data)
            st.write("🗣️ You said:", text)
        except Exception as e:
            st.error(f"❌ Speech Recognition Error: {e}")
            st.stop()

    # ----------------------------
    # Generate Gemini response
    # ----------------------------
    if st.button("🤖 Generate Response"):
        with st.spinner("Thinking..."):
            gemini_response = gemini.generate_content(text)
            answer = gemini_response.text
            st.write("🤖 Gemini says:", answer)

            # TTS output
            tts = gTTS(answer)
            tts.save("response.mp3")
            st.audio("response.mp3", format="audio/mp3")
