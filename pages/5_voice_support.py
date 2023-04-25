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
import pyodbc
from TTS.api import TTS

openai.api_key = os.getenv("OPENAI_API_KEY")
st.set_page_config(layout="wide")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = ""

if "cycle_state" not in st.session_state:   
    st.session_state.cycle_state = "To run"

if "user_profile" not in st.session_state:
    st.session_state.user_profile = ""

with open("./assets/voice_profile.json") as user_file:  # for ingestion JSON
    example_query = user_file.read()

AZURE_HOST = "tcp:pa-cme-primary-prod-sql-server.database.windows.net"
AZURE_USERNAME = "nps_profile"
AZURE_PASSWORD = "vOgGy%539"
AZURE_DATABASE = "pa-cme-primary-prod-db"

cnxn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};SERVER="
    + AZURE_HOST
    + ";DATABASE="
    + AZURE_DATABASE
    + ";UID="
    + AZURE_USERNAME
    + ";PWD="
    + AZURE_PASSWORD
)
cursor = cnxn.cursor()

query = "SELECT TOP 20 * FROM [dbo].[dispatch]"

cursor.execute(query)

user_database = pd.read_csv("./assets/dtv_profiles.csv")

img_business = iio.imread("./assets/DirecTV-Logo.jpg")
st.image(image=img_business, width=400)
img_business = iio.imread("./assets/AT&T_logo_2016.svg.png")
st.sidebar.image(image=img_business, width=200)

col1, col2 = st.columns(2)

col1.header("User Interface")
col2.header("Backend System")

# TTS model
#model_name = TTS.list_models()[0]
model_name = 'tts_models/en/ljspeech/tacotron2-DDC'
tts = TTS(model_name)

def text2voice(text,col,tts=tts):
    """translate text to voice with TTS and output chat history

    Args:
        text (str): Text to translate
        col (streamlit column): which column to output audio and chat history
    """    
    
    #tts.tts_to_file(text=text, speaker=tts.speakers[1], language=tts.languages[0], file_path="output.mp3",speed=1.5,  emotion='Happy')
    tts.tts_to_file(text=text,file_path="output.mp3",speed=1.5,  emotion='Happy')

    #output_tts.save("output.mp3")
    output_audio = open("output.mp3", "rb")
    col.write("System Output: ")
    col.audio(output_audio, format="audio/wav")
    col.text_area(label="Chat History", value=st.session_state.chat_history,height=400)
    
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
        col1.write("User Input: ")
        col1.audio(audio_bytes, format="audio/wav")

        JSON_prompt = f'Based on the request, create a JSON file with the same structure as the example JSON file. """\n\n\n Request: {user_input}, Example JSON: {example_query}. Possible values for Input Type field: 1. User Identification, 2. Add Channel, 3. Delete Channel 4. Channel Information, 5. Greet. Details about each field: 1. User Identification: when user provide first and last name. 2. Add Channel: When user wants to add/subscribe to a new channel. 3. Delete: When user wants to remove/unsubscribe to a channel. 4. Channel Information: When user ask about a channel. 5. Greet: When user greets."""\n\n\n'

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

        # perform action based on input type, match user in database
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
            col1.text_area(label="Chat History", value=st.session_state.chat_history,height=400)

            prompt = f'Extract the row from the pandas dataframe named user_database based on the input text. Store the results in a pandas dataframe called user_profile. \n  """ \n input text: {original_input}, user_database: {user_database} \n """ '
            # col2.write(prompt)
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
            col2.write("Executed Query: User Extraction (pandas dataframe): ")
            col2.code(pd_query)
            
            # Make sure local namespace variable is accessible outside the exec space
            loc = {}
            exec(pd_query, globals(), loc)
            user_profile = loc["user_profile"]
            st.session_state.user_profile = user_profile
            
            col2.write("User Profile: ")
            col2.write(st.session_state.user_profile)

        if input_JSON["Input Type"] == "Add Channel":

            original_input = input_JSON["Original Input"]
            user_profile = st.session_state.user_profile

            prompt = f'Based on the user profile, modify the pandas dataframe named user_profile given by the instructions and store the results in a dataframe named user_profile \n """\n\n\n user profile: {user_profile}, instructions: {input_JSON["Original Input"]} \n"""'
            # col2.write(prompt)
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

            loc = {"user_profile": user_profile}
            exec(pd_query, loc, globals())
            col2.write("Executed query: Add Channels")
            col2.code(pd_query)
            st.session_state.user_profile = loc["user_profile"]
            col2.write("User Profile")
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
            
            text2voice(text=output_text, col=col1,tts=tts)

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

            text2voice(text=output_text, col=col1, tts=tts)

        # Channel information is in SQL to showcase our abilities to talk to different system
        if input_JSON["Input Type"] == "Channel Information":
            
            original_input = input_JSON["Original Input"]
            prompt = f'Based on the question, query the mySQL database named channel_price \n """\n\n\n Question: {original_input} channel_price fields: channel, price \n"""'
            # col2.write(prompt)
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
            sql_query = response["choices"][0]["text"]

            col2.write(f"Executed query (SQL):")
            col2.code(sql_query)
            cursor.execute(sql_query)
            info = []
            for row in cursor:
                info.append(row)
            col2.write('Query Results')
            col2.code(info)
                
            prompt = f'Based on the question and information, inform the user in a friendly manner: \n """\n\n\n Question: {original_input}, Information: {info}\n"""'
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

            text2voice(text=output_text, col=col1, tts=tts)
            
if st.session_state.cycle_state == "To run":
    input_output_cycle()

