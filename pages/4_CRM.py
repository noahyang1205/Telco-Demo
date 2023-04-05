import streamlit as st
import openai
import imageio as iio
import os
import json
import pandas as pd

st.set_page_config(page_title="AT&T B2B chatbot", page_icon=":robot:")
df = pd.read_csv('./assets/b2b_profiles.csv')

img = iio.imread("./assets/AT&T_logo_2016.svg.png")
st.sidebar.image(image=img, width=200)

st.sidebar.dataframe(data=df)


openai.api_key = os.getenv("OPENAI_API_KEY")
img_business = iio.imread("./assets/AT&T_business.jpg")
st.image(image=img_business, width=500)

input_text = st.text_input("Input: ", value='', help='Try something like "Who is our largest customer by company size"')
st.session_state.current_response = input_text

with open("./assets/query.json") as user_file:
    example_query = user_file.read()

prompt = f"Based on the request, create a JSON file with the same structure as the example JSON file. Fill field with Unknown if you are unsure how to categorize the request. \"\"\"\n\n\n Request: {input_text}, Example JSON: {example_query}. Possible values for Database Field: 1. Product, 2. Promotion, 3. Customer, 4. Policy, 5.Operations, 6.Unknown. Possible values for Request Type field: 1. Query, 2. Modify  \"\"\"\n\n\n" 

df_columns = "First Name","Last Name","Position","Company","Sales play","Company size","Current customer","Current monthly spend","Industry","Address","City","State","Zipcode","Current products","Product needs","Start date","Contract end date","Contract end year","Competitive options","Current provider"

if input_text:

    responses = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            temperature=0,
            max_tokens=1024,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=["Q:"],
            timeout=20)
    #- st.write(prompt)
    txt_response = responses["choices"][0]["text"]
    json_response = json.loads(txt_response)
    json.dumps(json_response, indent=4)
    
    with st.expander(label='See Ingestion JSON'):
        st.code(txt_response, language='json')
    origianl_prompt = json_response['Original Request']
    
    if json_response['Database'] == 'Customer': 
        if json_response['Request Type'] == 'Query':
            prompt = f'Perform the request to the pandas dataframe named df. Store results in a variable named results_df: \n \"\"\"\n\n\n Request: {origianl_prompt}, Dataframe columns: {df_columns} \"\"\"\n'
            
            pd_responses = openai.Completion.create(
                model="text-davinci-003",
                prompt=prompt,
                temperature=0,
                max_tokens=1024,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                stop=["Q:"],
                timeout=20)
            
            exec_code = pd_responses["choices"][0]["text"]
            st.write(f'Executed query: {exec_code}')
            exec(exec_code)
            st.write(results_df)

            output_prompt = f"Rewrite the following pandas dataframe into natural language \"\"\"\n\n\n {results_df} \"\"\"\n"
            if json_response['Request Type'] == 'Query':
                output_responses = openai.Completion.create(
                    model="text-davinci-003",
                    prompt=output_prompt,
                    temperature=0,
                    max_tokens=1024,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0,
                    stop=["Q:"],
                    timeout=20)
                st.text_area('Query results',output_responses["choices"][0]["text"])
    if json_response['Request Type'] == "Modify": 
        prompt = f'Modify the pandas dataframe named df according to the request: \n \"\"\"\n\n\n Request: {origianl_prompt}, Dataframe columns: {df_columns} \"\"\"\n'
        
        pd_responses = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            temperature=0,
            max_tokens=1024,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=["Q:"],
            timeout=20)
        
        exec_code = pd_responses["choices"][0]["text"]
        st.write(f'Executed query: {exec_code}')
        exec(exec_code)
        st.write(df)