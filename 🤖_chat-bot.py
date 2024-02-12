import streamlit as st
from streamlit_chat import message
import os
from pathlib import Path
from io import StringIO
import imageio as iio
from streamlit_extras.app_logo import add_logo
from datetime import date
from openai import OpenAI
import openai

client = OpenAI()
st.set_page_config(page_title="Telco chat-bot demo", page_icon=":robot:")

openai.api_key = os.getenv("OPENAI_API_KEY")

st.header("Telco Chat Log")

if "generated" not in st.session_state:
    st.session_state["generated"] = []

if "past" not in st.session_state:
    st.session_state["past"] = []


img = iio.imread("./assets/telstra-logo.png")
st.sidebar.header("Telecom Co.")

st.sidebar.markdown("# User profile parameters")

# User profile/model parameters on the sidebar
preset_profiles = os.listdir("user_profiles")
preset_profiles.append("Customized profile")
profile_selection = st.sidebar.selectbox(
    "Select user profile", (preset_profiles), index=1
)


if profile_selection == "Customized profile":
    expander = st.sidebar.expander("Customize Profile")
    cp_name = st.sidebar.text_input("Profile name", "Brian Anderson")
    cp_age = st.sidebar.slider(
        label="Profile Age", min_value=18, max_value=99, step=1, value=25
    )
    cp_address = st.sidebar.text_input("Profile Address", "123 Cherry St, Seattle, WA")
    cp_family = st.sidebar.selectbox(
        "Profile family Status",
        ("Single", "Married, No children", "Married, With children"),
    )
    cp_phone = st.sidebar.text_input("Profile phone number", "(245) 345-3456")
    cp_occupation = st.sidebar.text_input("Profile occupation", "Teacher")
    cp_plan = st.sidebar.selectbox(
        "Profile Plan",
        (
            "Unlimited Data Plan",
            "Small Data Plan",
            "Family Plan",
            "International Plan",
            "Senior Plan",
            "Student Plan",
            "Talk and Text Plan",
            "Prepaid Plan",
        ),
    )
    cp_comments = st.sidebar.text_input("Additional Comments", "")

    profile_data = "\n".join(
        [
            "Name: " + cp_name,
            "Current plan: " + cp_plan,
            "Age: " + str(cp_age),
            "Address: " + cp_address,
            "Family Status: " + cp_family,
            "Phone Number: " + cp_phone,
            "Occupation: " + cp_occupation,
            "Additional comments: " + cp_comments,
        ]
    )
    expander.write(profile_data)

else:
    expander = st.sidebar.expander("See user profile details")
    profile_data = Path(os.path.join("./user_profiles", profile_selection)).read_text(
        "UTF-8"
    )
    expander.write(profile_data)

policy_data = Path(os.path.join("policy.txt")).read_text("UTF-8")
expander = st.sidebar.expander("See policy")
expander.write(policy_data)

# st.sidebar.write('## ')
st.sidebar.markdown("# Chatbot parameters")

ft_model_name, non_ft_model_name, chat_model = (
    "Fine-tuned model: ada:ft-bain-data-science-2023-03-02-00-53-43",
    "Non-fine-tuned model: text-davinci-003",
    "gpt-4",
)

option = st.sidebar.selectbox(
    "Select models", (non_ft_model_name, ft_model_name, chat_model), index=2
)
print(option)

attitude = st.sidebar.select_slider(
    "Select a chatbot attitude",
    options=["Conservative", "Neutral", "Slightly Generous", "Very Generous"],
)

if attitude == "Conservative":
    attitude_prompt = "Under no circumstances will you offer any credits to the customer. You will tell the customer explicitly that a customer support chatbot cannot offer any credits and Telco does not have a credit policy"
elif attitude == "Neutral":
    attitude_prompt = "When the customer asks for credit, refer the customer to a live sales representative"
elif attitude == "Slightly Generous":
    attitude_prompt = "Offer the customer a $5 credit in a bill dispute situation when asked by the customer. Offer $30 credit as a retention incentive when the customer wants to terminate his/her plans. Only provide this information when asked by customer"
elif attitude == "Very Generous":
    attitude_prompt = "Offer the customer a $40 credit in a bill dispute situation when asked by the customer. Offer a free month of service as a retention incentive when the customer wants to terminate his/her plans. "

today = date.today()

assistant_context = f"You are respectful, welcoming, kind, understanding, professional, truthful, reserved. You are an Telstra customer support AI assistant. Your goal is to answer my questions as accurately as possible and use customer profile data and policy data I provide to help answer them. Do not make up facts or answer questions outside of the scope of customer support. If you are not sure about a question, refer the customer to Telco website at https://www.Telco.com.au/ or call the Telco customer support at 1 (877) 835-7872. Today is {today}\n"
assistant_context = assistant_context + attitude_prompt + profile_data + policy_data

expander = st.sidebar.expander("See chatbot personality")
expander.write(assistant_context)

temperature = st.sidebar.slider(
    label="Model temperature", min_value=0.0, max_value=1.0, step=0.01, value=0.0
)


def query(prompt):

    # openAI_prompt = bd_chat_lines_context + "\n" + prompt["inputs"]["text"] + "\n"
    user_prompt = prompt["inputs"]["text"]

    if option == chat_model:
        # response = openai.ChatCompletion.create(
        #     model="gpt-3.5-turbo",
        #     prompt=openAI_prompt,
        #     temperature=temperature,
        #     max_tokens=512,
        #     top_p=1,
        #     frequency_penalty=0,
        #     presence_penalty=0,
        #     stop=["Q:"],
        #     timeout=20,
        # )
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": assistant_context},
                {"role": "user", "content": user_prompt},
            ],
        )
    elif option == non_ft_model_name:
        # print('Non ft model')
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=assistant_context,
            temperature=temperature,
            max_tokens=512,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=["Q:"],
            timeout=20,
        )
    elif option == ft_model_name:
        # print('FT model')
        response = openai.Completion.create(
            model="ada:ft-bain-data-science-2023-03-02-00-53-43",
            prompt=assistant_context,
            temperature=temperature,
            max_tokens=511,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=["Q:"],
            timeout=20,
        )

    response_text = response.choices[0].message.content
    # response_text = response_text.replace("A:", "")
    # response_text = response_text.replace("\n", "")

    prompt["inputs"]["generated_responses"].append(response_text)

    return prompt


def get_text():
    input_text = st.text_input("Enter Text here: ", key="input")
    return input_text


user_input = get_text()
print(len(st.session_state["past"]))
print(len(st.session_state["generated"]))
if user_input:
    output = query(
        prompt={
            "inputs": {
                "past_user_inputs": st.session_state.past,
                "generated_responses": st.session_state.generated,
                "text": user_input,
            },
            "parameters": {"repetition_penalty": 0},
        }
    )
    generated_response = output["inputs"]["generated_responses"]

    if "past" not in st.session_state or "generated" not in st.session_state:
        st.session_state["generated"] = []
        st.session_state["past"] = []
    else:
        st.session_state.past.append(user_input)
    try:
        st.session_state.generated.append(output["generated_text"])
    except:
        output["generated_text"] = []

if "past" in st.session_state and "generated" in st.session_state:
    if len(st.session_state["past"]) >= len(st.session_state["generated"]):
        for i in range(len(st.session_state["generated"]) - 1, -1, -1):

            message(st.session_state["generated"][i], key=str(i))
            message(st.session_state["past"][i], is_user=True, key=str(i) + "_user")
    elif len(st.session_state["past"]) < len(st.session_state["generated"]):
        st.session_state["generated"].pop()

if len(st.session_state["past"]) == 0:
    print("Past len is zero")
    st.session_state["generated"] = []
    st.session_state["past"] = []
elif "generated" not in st.session_state or "past" not in st.session_state:
    st.session_state["generated"] = []
    st.session_state["past"] = []
