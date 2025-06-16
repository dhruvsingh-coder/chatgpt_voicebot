import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
from gtts import gTTS
import io
import speech_recognition as sr
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase

# === Load env ===
if "GEMINI_API_KEY" in st.secrets:
    gemini_api_key = st.secrets["GEMINI_API_KEY"]
else:
    load_dotenv()
    gemini_api_key = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=gemini_api_key)
gemini_model = genai.GenerativeModel("gemini-2.0-flash")

st.set_page_config(page_title="🎙️ Gemini Voice Bot")
st.title("🎙️ Gemini Voice Bot")

st.write("🎤 Click Start to record your question in your browser:")

# === Use streamlit-webrtc ===
class AudioProcessor(AudioProcessorBase):
    def recv(self, frame):
        return frame  # required by the interface but not used here

ctx = webrtc_streamer(
    key="speech",
    mode="SENDRECV",
    audio_receiver_size=256,
    media_stream_constraints={"video": False, "audio": True},
    async_processing=True,
)

if ctx.audio_receiver:
    import av
    audio_frames = ctx.audio_receiver.get_frames(timeout=1)
    wav_buffer = io.BytesIO()
    with av.open(wav_buffer, mode='w', format='wav') as wf:
        for frame in audio_frames:
            wf.write(frame)
    wav_buffer.seek(0)
    st.audio(wav_buffer, format="audio/wav")

    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_buffer) as source:
        audio_data = recognizer.record(source)
        try:
            question = recognizer.recognize_google(audio_data)
            st.write(f"**You said:** {question}")

            # Gemini response
            response = gemini_model.generate_content(question)
            answer = response.text
            st.write(f"**Gemini:** {answer}")

            # TTS in-memory
            tts = gTTS(answer)
            mp3_fp = io.BytesIO()
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)

            st.audio(mp3_fp, format="audio/mp3")

        except Exception as e:
            st.error(f"Could not process audio: {e}")
