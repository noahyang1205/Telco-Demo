import streamlit as st
from audio_recorder_streamlit import audio_recorder
import imageio as iio
import openai
import soundfile as sf
import io
import gtts
import os

openai.api_key = os.getenv("OPENAI_API_KEY")
st.set_page_config(layout="wide")

img_business = iio.imread("./assets/DirecTV-Logo.jpg")
st.image(image=img_business, width=400)
img_business = iio.imread("./assets/AT&T_logo_2016.svg.png")
st.sidebar.image(image=img_business, width=200)


audio_bytes = audio_recorder()
if audio_bytes:
    #st.audio(audio_bytes, format="audio/wav")

    audio_data, samplerate = sf.read(io.BytesIO(audio_bytes))
    sf.write('audio_input.mp3', audio_data, samplerate)
    audio_file= open("audio_input.mp3", "rb")

    transcript = openai.Audio.transcribe("whisper-1", audio_file)

    user_input = transcript['text']

    st.write(user_input)
    st.audio(audio_bytes, format="audio/wav")
    response = openai.Completion.create(
            model="text-davinci-003",
            prompt=user_input,
            temperature=0,
            max_tokens=2024,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            timeout=20,
        )
    output_text = response["choices"][0]["text"]

    st.write(output_text)
    output_tts = gtts.gTTS(output_text)
    output_tts.save("output.mp3")
    output_audio = open("output.mp3", "rb")
    st.audio(output_audio, format="audio/wav")