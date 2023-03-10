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




#`add_logo("./assets/logo.png")

openai.api_key = os.getenv('OPENAI_API_KEY')

st.header("Telco Chat Log")

if 'generated' not in st.session_state:
    st.session_state['generated'] = []

if 'past' not in st.session_state:
    st.session_state['past'] = []
    

img = iio.imread('./assets/logo.png')
st.sidebar.image(image=img)
st.sidebar.markdown("# Chat-bot parameters")

preset_profiles = os.listdir('user_profiles')
print(type(preset_profiles))
preset_profiles.append('Customized profile')
print(preset_profiles)
profile_selection = st.sidebar.selectbox('Select user profile',(preset_profiles),index=0)


if profile_selection == 'Customized profile':
    expander = st.sidebar.expander("Customize Profile")
    cp_name = st.sidebar.text_input('Profile name', 'Brian Anderson')
    cp_age = st.sidebar.slider(label='Profile Age',min_value=18, max_value=99, step=1, value=25)
    cp_address = st.sidebar.text_input('Profile Address', '123 Cherry St, Seattle, WA')
    cp_family = st.sidebar.selectbox('Profile family Status', ('Single', 'Married, No children', 'Married, With children'))
    cp_phone = st.sidebar.text_input('Profile phone number', '(245) 345-3456')
    cp_occupation = st.sidebar.text_input('Profile occupation', 'Teacher')
    cp_plan = st.sidebar.selectbox('Profile Plan', ('Unlimited Data Plan', 'Small Data Plan', 'Family Plan', 'International Plan', 'Senior Plan', 'Student Plan', 'Talk and Text Plan', 'Prepaid Plan'))
    cp_comments = st.sidebar.text_input('Additional Comments', '')
    
    
    profile_data = "\n".join(['Name: '+cp_name, "Current plan: "+cp_plan, "Age: "+str(cp_age), "Address: "+cp_address, "Family Status: "+cp_family, "Phone Number: "+cp_phone, "Occupation: "+cp_occupation, 'Additional comments: '+cp_comments])
    expander.write(profile_data)

    

else:
    expander = st.sidebar.expander("See user profile details")
    profile_data = Path(os.path.join('./user_profiles', profile_selection)).read_text("UTF-8")
    expander.write(profile_data)

policy_data = Path(os.path.join('policy.txt')).read_text("UTF-8")
expander = st.sidebar.expander("See policy")
expander.write(policy_data)


assistant_context = 'You are respectful, welcoming, kind, understanding, professional, truthful, honest. You are an AT&T customer support AI assistant. Your goal is to answer my questions as accurately as possible and use customer profile data and policy data I provide to help answer them. Do not make up facts or answer questions outside of the scope of customer support. If you are not sure about a question, refer the customer to AT&T website or call the AT&T customer support'

bd_chat_lines_context = assistant_context + profile_data + policy_data



#st.sidebar.write("## Upload Context File")


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

# uploaded_file = st.sidebar.file_uploader("Upload context file")

# bd_chat_lines_context = ''

# if uploaded_file is None: # If no context file is provided, defaults to using the context file in directory
#     bd_chat_lines_context = Path('./context.txt').read_text("UTF-8")
#     tokens = bd_chat_lines_context.split()
#     if len(tokens) > 900:
#         st.sidebar.write('Document token exceeds limit, truncating....')
#         tokens = tokens[:900]      
#     bd_chat_lines_context = ''.join(tokens)
    
#     st.sidebar.write('No context file uploaded, defaulting to Sarah Smith')
# else: 
#     stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
#     bd_chat_lines_context = stringio.getvalue()
#     tokens = bd_chat_lines_context.split()
    
#     print(len(tokens))
#     if len(tokens) > 900:
#         st.sidebar.write('Document token exceeds limit, truncating....')
#         tokens = tokens[:900]      
#     bd_chat_lines_context = ''.join(tokens)

# expander = st.sidebar.expander("See uploaded context")
# expander.write(bd_chat_lines_context)