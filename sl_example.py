import streamlit as st
from streamlit_chat import message
import requests
import os
import openai
from pathlib import Path

st.set_page_config(
    page_title="Streamlit Chat - Demo",
    page_icon=":robot:"
)

#API_URL = "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill"
#headers = {"Authorization": st.secrets['api_key']}

openai.api_key = os.getenv('OPENAI_API_KEY')

st.header("Sarah Smith's Chat Log")
#st.markdown("[Github](https://github.com/ai-yash/st-chat)")

if 'generated' not in st.session_state:
    st.session_state['generated'] = []

if 'past' not in st.session_state:
    st.session_state['past'] = []
    
    
###############################################################
# def query(payload):
# 	response = requests.post(API_URL, headers=headers, json=payload)
# 	return response.json()
###############################################################

def query(prompt):
    # print(prompt)
    # print(type(prompt))
    bd_chat_lines_context = Path('context.txt').read_text("UTF-8")
    #query = 'Why should I choose AT&T'
    #print(prompt['inputs']['text'])
    openAI_prompt = bd_chat_lines_context + "\n" + prompt['inputs']['text'] + "\n"
    
    #print(prompt)
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=openAI_prompt,
        temperature=0.0,
        max_tokens=512,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=["Q:"],
        timeout=20
    )
    response_text = response["choices"][0]["text"]
    response_text = response_text.replace("A:", "")
    response_text = response_text.replace("\n", "")
    
    prompt["inputs"]["generated_responses"].append(response_text) 
    
    return prompt


def get_text():
    input_text = st.text_input("You: ", key="input")
    return input_text 


user_input = get_text()
#print(st.session_state.generated)
if user_input:
    output = query(prompt={
        "inputs": {
            "past_user_inputs": st.session_state.past,
            "generated_responses": st.session_state.generated,
            "text": user_input,
        },"parameters": {"repetition_penalty": 1.33}, 
    })
    generated_response = output['inputs']['generated_responses']
    #print(f'generated responses {generated_response}')
    st.session_state.past.append(user_input)
    #print(f'prompt {output}')

    try:
        st.session_state.generated.append(output["generated_text"])
    except:
        output["generated_text"] = []
 
if st.session_state['generated']:
    for i in range(len(st.session_state['generated'])-1, -1, -1):
        # if len(st.session_state["past"]) == 1:
        #     st.session_state.past.append([])
        print(st.session_state["generated"])
        print(st.session_state["past"])
        print(i)
        message(st.session_state["generated"][i], key=str(i))
        message(st.session_state['past'][i], is_user=True, key=str(i) + '_user')

# if st.session_state['generated']:
#     session_state_generated = st.session_state['generated']
#     print(f'Session state generated {session_state_generated}')
#     for i in range(len(st.session_state['generated'])-1, -1, -1):
#         message(st.session_state["generated"][i], key=str(i))
#         print(f'i: {i}')
#         print(st.session_state["generated"])
#         print(st.session_state['past'])
        
#         #if len(st.session_state['past']) > i:  
#         message(st.session_state['past'][i-1], is_user=True, key=str(i) + '_user')
        