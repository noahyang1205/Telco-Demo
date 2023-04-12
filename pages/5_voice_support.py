import streamlit as st
from audio_recorder_streamlit import audio_recorder
import imageio as iio
import openai
import soundfile as sf
import io
import gtts
import os
import pandas as pd
import json

openai.api_key = os.getenv("OPENAI_API_KEY")
st.set_page_config(layout="wide")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = ""

if "cycle_state" not in st.session_state:
    st.session_state.cycle_state = "To run"

if "user_profile" not in st.session_state:
    st.session_state.user_profile = ""

with open("./assets/voice_profile.json") as user_file: # for ingestion JSON
    example_query = user_file.read()

user_database = pd.read_csv("./assets/dtv_profiles.csv")

img_business = iio.imread("./assets/DirecTV-Logo.jpg")
st.image(image=img_business, width=400)
img_business = iio.imread("./assets/AT&T_logo_2016.svg.png")
st.sidebar.image(image=img_business, width=200)

col1, col2 = st.columns(2)

col1.header("User Interface")
col2.header("Backend System")

def input_output_cycle():
    """One cycle of user input and AI response, a cycle consists of the following steps:
        1. Record user audio input, transcribe to text
        2. Transform input text to structured JSON
        3. Based on JSON, generate response and perform action 
        4. Translate AI text response to speech
    """
    audio_bytes = audio_recorder()
    if audio_bytes:
        audio_data, samplerate = sf.read(io.BytesIO(audio_bytes))
        sf.write("audio_input.mp3", audio_data, samplerate)
        audio_file = open("audio_input.mp3", "rb")
        transcript = openai.Audio.transcribe(
            "whisper-1", audio_file
        )  # translate audio to text
        user_input = transcript["text"]

        st.session_state.chat_history += (
            f"User: {user_input} \n"  # append current transcribed text to chat history
        )
        col1.audio(audio_bytes, format="audio/wav")

        JSON_prompt = f'Based on the request, create a JSON file with the same structure as the example JSON file. """\n\n\n Request: {user_input}, Example JSON: {example_query}. Possible values for Input Type field: 1. User Identification, 2. Add Channel, 3. Delete Channel 4. Account/Service Inquiry, 5. Greet """\n\n\n'

        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=JSON_prompt,
            temperature=0,
            max_tokens=2024,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            timeout=20,
        )
        text_JSON = response["choices"][0]["text"]
        input_JSON = json.loads(text_JSON)
        json.dumps(input_JSON, indent=4)
        col2.write("Ingestion JSON")
        col2.code(input_JSON)

        # perform action based on input type
        if input_JSON["Input Type"] == "User Identification":

            original_input = input_JSON["Original Input"]
            prompt = f'Extract the user profile from the pandas dataframe based on the input text. Convey the channel information to the user in a friendly and welcoming fashion: """\n\n\n input text: {original_input}, database: {user_database} \n"""'

            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=prompt,
                temperature=0,
                max_tokens=2024,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                timeout=20,
            )
            output_text = response["choices"][0]["text"].strip()

            st.session_state.chat_history += (
                f"AI response: {output_text} \n"  # append AI response to chat history
            )

            output_tts = gtts.gTTS(output_text)
            output_tts.save("output.mp3")
            output_audio = open("output.mp3", "rb")
            col1.audio(output_audio, format="audio/wav")
            col1.text_area(label="Chat History", value=st.session_state.chat_history)
            
            prompt = f'Extract the row from the pandas dataframe named user_database based on the input text. Store the results in a pandas dataframe called user_profile. \n  """ \n input text: {original_input}, user_database: {user_database} \n """ '
            #col2.write(prompt)
            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=prompt,
                temperature=0,
                max_tokens=512,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                timeout=20,
            )
            pd_query = response["choices"][0]["text"]
            col2.write("Executed Query: User Extraction")
            
            col2.code(pd_query)
            #multi-line program
            #exec_code = compile(pd_query,'something', 'exec')
            loc = {}
            exec(pd_query, globals(),loc)
            #exec(pd_query)
            user_profile = loc['user_profile']
            
            print(user_profile)
            
            st.session_state.user_profile = user_profile
            col2.write('User Profile: ')
            col2.write(st.session_state.user_profile)
            
            
        if input_JSON["Input Type"] == "Add Channel":

            original_input = input_JSON["Original Input"]
            
            user_profile = st.session_state.user_profile
            
            prompt = f'Based on the user profile, modify the pandas dataframe named user_profile given by the instructions and store the results in a dataframe named user_profile \n """\n\n\n user profile: {user_profile}, instructions: {input_JSON["Original Input"]} \n"""'
            #col2.write(prompt)
            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=prompt,
                temperature=0,
                max_tokens=512,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                timeout=20,
            )
            pd_query = response["choices"][0]["text"]
            
            loc = {'user_profile':user_profile}
            exec(pd_query, loc, globals())
            col2.write('Executed query: Add Channels')
            col2.code(pd_query)
            st.session_state.user_profile = loc['user_profile']
            col2.write('User Profile')
            col2.write(st.session_state.user_profile)
            
            prompt = f'Let the user know his/her that you have fulfilled the request and let them know their current subscribe channel from the database in a friendly manner: """\n user: {st.session_state.user_profile}, request: {input_JSON["Original Input"]}\n""" '

            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=prompt,
                temperature=0,
                max_tokens=512,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                timeout=20,
            )
            output_text = response["choices"][0]["text"].strip()

            st.session_state.chat_history += (
                f"AI response: {output_text} \n"  # append AI response to chat history
            )

            output_tts = gtts.gTTS(output_text)
            output_tts.save("output.mp3")
            output_audio = open("output.mp3", "rb")
            col1.audio(output_audio, format="audio/wav")
            # col1.write(st.session_state.chat_history)
            col1.text_area(label="Chat History", value=st.session_state.chat_history)

        if input_JSON["Input Type"] == "Greet":
            prompt = "You are a Direct TV customer support chatbot. Greet the user and ask for his/her first and last name"

            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=prompt,
                temperature=0,
                max_tokens=2024,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                timeout=20,
            )
            output_text = response["choices"][0]["text"].strip()

            st.session_state.chat_history += (
                f"AI response: {output_text} \n"  # append AI response to chat history
            )

            output_tts = gtts.gTTS(output_text)
            output_tts.save("output.mp3")
            output_audio = open("output.mp3", "rb")
            col1.audio(output_audio, format="audio/wav")
            # col1.write(st.session_state.chat_history)
            col1.text_area(label="Chat History", value=st.session_state.chat_history)


if st.session_state.cycle_state == "To run":
    input_output_cycle()

