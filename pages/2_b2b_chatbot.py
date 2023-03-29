import streamlit as st
from streamlit_chat import message
import os
import openai
from pathlib import Path
from io import StringIO
import imageio as iio
from streamlit_extras.app_logo import add_logo
from datetime import date
import json

st.set_page_config(
    page_title="AT&T B2B chatbot",
    page_icon=":robot:"
)

openai.api_key = os.getenv('OPENAI_API_KEY')

img_business = iio.imread('./assets/AT&T_business.jpg')
st.image(image=img_business, width=500)

st.markdown("## B2B Agent Chat Log")

if 'generated' not in st.session_state:
    st.session_state['generated'] = []

if 'past' not in st.session_state:
    st.session_state['past'] = []

img = iio.imread('./assets/AT&T_logo_2016.svg.png')
st.sidebar.image(image=img, width=200)

policy_data = Path(os.path.join('./assets/atnt_policy.txt')).read_text("UTF-8")
#account_data = Path(os.path.join('./assets/atnt_account_info.txt')).read_text("UTF-8")

with open('./assets/b2b_profile.json') as user_file:
    account_data = user_file.read()


temperature = st.sidebar.slider(label='Model temperature',min_value=0.0, max_value=1.0, step=0.01, value=0.0)


with st.sidebar.expander("See policy data"):
    st.text_area('Policy data', policy_data, height=400)

with st.sidebar.expander("See account data"):
    st.text_area('Account data', account_data, height=400)


today = date.today()

bd_chat_lines_context = f'You are a AT&T B2B agent support assistant. Your job is to answer questions using the information database \n """{account_data}"""  and the following AT&T policies: \n """{policy_data}""" . Some of the accounts in the database are not current AT&T customers. Today is {today}'
print(bd_chat_lines_context)


def query(prompt):
        
    openAI_prompt = bd_chat_lines_context + "\n" + prompt['inputs']['text'] + "\n"
    
    print('Non ft model')
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=openAI_prompt,
        temperature=temperature,
        max_tokens=2024,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        timeout=20
    )

    response_text = response["choices"][0]["text"]
    response_text = response_text.replace("A:", "")
    response_text = response_text.replace("\n", "")
    
    prompt["inputs"]["generated_responses"].append(response_text) 
    
    return prompt

def get_text():
    input_text = st.text_input("Enter Text here: ", key="input")
    return input_text 


user_input = get_text()

if user_input:
    output = query(prompt={
        "inputs": {
            "past_user_inputs": st.session_state.past,
            "generated_responses": st.session_state.generated,
            "text": user_input,
        },"parameters": {"repetition_penalty": 0}, 
    })
    generated_response = output['inputs']['generated_responses']
    st.session_state.past.append(user_input)

    try:
        st.session_state.generated.append(output["generated_text"])
    except:
        output["generated_text"] = []

if st.session_state['generated'] and st.session_state["past"]:
    for i in range(len(st.session_state['generated'])-1, -1, -1):

        # print(st.session_state["generated"])
        # print(st.session_state["past"])
        # print(i)
        message(st.session_state["generated"][i], key=str(i))
        message(st.session_state['past'][i], is_user=True, key=str(i) + '_user',  avatar_style="adventurer")    
if len(st.session_state['past']) == 0:
    print('Past len is zero')
    st.session_state['generated'] = []
    st.session_state['past'] = []