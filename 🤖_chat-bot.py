import streamlit as st
from streamlit_chat import message
import os
import openai
from pathlib import Path
from io import StringIO
import imageio as iio
from streamlit_extras.app_logo import add_logo

st.set_page_config(
    page_title="Telco chat-bot demo",
    page_icon=":robot:"
)




#add_logo("./assets/logo.png")

openai.api_key = os.getenv('OPENAI_API_KEY')

st.header("Telco Chat Log")

if 'generated' not in st.session_state:
    st.session_state['generated'] = []

if 'past' not in st.session_state:
    st.session_state['past'] = []
    

img = iio.imread('./assets/logo.png')
st.sidebar.image(image=img)
st.sidebar.markdown("# Chat-bot parameters")
#st.sidebar.write("## Upload Context File")
uploaded_file = st.sidebar.file_uploader("Upload context file")

bd_chat_lines_context = ''

if uploaded_file is None: # If no context file is provided, defaults to using the context file in directory
    bd_chat_lines_context = Path('./context.txt').read_text("UTF-8")
    tokens = bd_chat_lines_context.split()
    if len(tokens) > 900:
        st.sidebar.write('Document token exceeds limit, truncating....')
        tokens = tokens[:900]      
    bd_chat_lines_context = ''.join(tokens)
    
    st.sidebar.write('No context file uploaded, defaulting to Sarah Smith')
else: 
    stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
    bd_chat_lines_context = stringio.getvalue()
    tokens = bd_chat_lines_context.split()
    
    print(len(tokens))
    if len(tokens) > 900:
        st.sidebar.write('Document token exceeds limit, truncating....')
        tokens = tokens[:900]      
    bd_chat_lines_context = ''.join(tokens)

expander = st.sidebar.expander("See uploaded context")
expander.write(bd_chat_lines_context)

#st.sidebar.write('## ')

ft_model_name, non_ft_model_name ='Fine-tuned model: ada:ft-bain-data-science-2023-03-02-00-53-43', 'Non-fine-tuned model: text-davinci-003'

option = st.sidebar.selectbox('Select models',(non_ft_model_name,ft_model_name),index=0)
print(option)

temperature = st.sidebar.slider(label='Model temperature',min_value=0.0, max_value=1.0, step=0.01, value=0.0)

def query(prompt):
        
    openAI_prompt = bd_chat_lines_context + "\n" + prompt['inputs']['text'] + "\n"
        
    if option == non_ft_model_name:
        print('Non ft model')
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=openAI_prompt,
            temperature=temperature,
            max_tokens=511,
            top_p=1,
            frequency_penalty=1.33,
            presence_penalty=0,
            stop=["Q:"],
            timeout=20
        )
    elif option == ft_model_name:
        print('FT model')
        response = openai.Completion.create(
            model="ada:ft-bain-data-science-2023-03-02-00-53-43",
            prompt=openAI_prompt,
            temperature=temperature,
            max_tokens=511,
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
 
if st.session_state['generated']:
    for i in range(len(st.session_state['generated'])-1, -1, -1):

        print(st.session_state["generated"])
        print(st.session_state["past"])
        print(i)
        message(st.session_state["generated"][i], key=str(i))
        message(st.session_state['past'][i], is_user=True, key=str(i) + '_user')

        