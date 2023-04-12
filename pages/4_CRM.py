import streamlit as st
import openai
import imageio as iio
import os
import json
import pandas as pd
from datetime import date
import pyodbc

st.set_page_config(page_title="AT&T B2B chatbot", page_icon=":robot:",layout="wide")
df = pd.read_csv("./assets/b2b_profiles.csv")
dispatch_df = pd.read_csv("./assets/dispatch.csv")

img = iio.imread("./assets/AT&T_logo_2016.svg.png")
st.sidebar.image(image=img, width=200)

with st.sidebar.expander(label="See customer database"):
    st.dataframe(data=df)
df["Contract end date"] = pd.to_datetime(df["Contract end date"])
df["Contract start date"] = pd.to_datetime(df["Contract start date"])
with st.sidebar.expander(label="See dispatch database"):
    st.dataframe(data=dispatch_df)
dispatch_df["Date"] = pd.to_datetime(dispatch_df["Date"])


openai.api_key = os.getenv("OPENAI_API_KEY")
img_business = iio.imread("./assets/AT&T_business.jpg")
st.image(image=img_business, width=500)

##-----------------------
## Database Configuration
##-----------------------

# Add credentials to .env and update .gitignore for commit

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
# for row in cursor:
#     st.write(row)


col1,col2 = st.columns(2)

col1.header('User Interface')
col2.header('System Backend')

input_text = col1.text_input(
    "Input: ",
    value="",
    help='Try something like "What are the routes for dispatched trucks this week?"',
)


st.session_state.current_response = input_text

with open("./assets/query.json") as user_file:
    example_query = user_file.read()

prompt = f'Based on the request, create a JSON file with the same structure as the example JSON file. Fill field with Unknown if you are unsure how to categorize the request. """\n\n\n Request: {input_text}, Example JSON: {example_query}. Possible values for Database Field: 1. Product, 2. Promotion, 3. Customer, 4. Policy, 5.Operations/Dispatch, 6.Unknown. Possible values for Request Type field: 1. Query, 2. Modify  """\n\n\n'

df_columns = (
    "First Name",
    "Last Name",
    "Position",
    "Company",
    "Sales play",
    "Company size",
    "Current customer",
    "Current monthly spend",
    "Industry",
    "Address",
    "City",
    "State",
    "Zipcode",
    "Current products",
    "Product needs",
    "Contract start date",
    "Contract end date",
    "Contract end year",
    "Competitive options",
    "Current provider",
)

dispatch_columns = [
    "Dispatch_ID",
    "Date",
    "Customer_ID",
    "Customer_Name",
    "Location_ID",
    "Address",
    "Operation",
    "Truck_ID",
    "Scheduled_Start_Time",
    "Scheduled_End_Time",
    "Priority",
    "Start_Time",
    "End_Time",
]


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
        timeout=20,
    )
    txt_response = responses["choices"][0]["text"]
    json_response = json.loads(txt_response)
    json.dumps(json_response, indent=4)

    col2.write('Ingestion JSON: ')
    col2.code(txt_response, language="json")
    original_prompt = json_response["Original Request"]

    if json_response["Database"] == "Customer":
        if json_response["Request Type"] == "Query":
            prompt = f'Perform the request to the pandas dataframe named df. Store results in a variable named results_df: \n """\n\n\n Request: {original_prompt}, Dataframe columns: {df_columns} """\n'

            pd_responses = openai.Completion.create(
                model="text-davinci-003",
                prompt=prompt,
                temperature=0,
                max_tokens=1024,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                stop=["Q:"],
                timeout=20,
            )

            exec_code = pd_responses["choices"][0]["text"]
            
            col2.write(f"Executed query")
            col2.code(exec_code)
            exec(exec_code)
            # st.write(results_df)

            output_prompt = f'Use the following pandas dataframe to answer the question in natural language"""\n\n\n pandas dataframe: {results_df}, question: {json_response["Original Request"]}"""\n'
            # st.write(output_prompt)
            if json_response["Request Type"] == "Query":
                output_responses = openai.Completion.create(
                    model="text-davinci-003",
                    prompt=output_prompt,
                    temperature=0,
                    max_tokens=1024,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0,
                    stop=["Q:"],
                    timeout=20,
                )
                col1.text_area("Query results", output_responses["choices"][0]["text"])
        if json_response["Request Type"] == "Modify":
            prompt = f'Modify the pandas dataframe named df according to the request: \n """\n\n\n Request: {original_prompt}, Dataframe columns: {df_columns}"""\n'

            pd_responses = openai.Completion.create(
                model="text-davinci-003",
                prompt=prompt,
                temperature=0,
                max_tokens=1024,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                stop=["Q:"],
                timeout=20,
            )

            exec_code = pd_responses["choices"][0]["text"]
            col2.code(f"Executed query")
            col2.code(exec_code)
            exec(exec_code)
            col1.write(df)

    if json_response["Database"] == "Operations/Dispatch":

        today = date.today().strftime("%m/%d/%Y")
        if json_response["Request Type"] == "Query":

            prompt = f'Perform the request to the mySQL database named dispatch. Today is {today}: \n """\n\n\n Request: {original_prompt}, SQL fields: {dispatch_columns} """\n'
            pd_responses = openai.Completion.create(
                model="text-davinci-003",
                prompt=prompt,
                temperature=0,
                max_tokens=1024,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                stop=["Q:"],
                timeout=20,
            )

            exec_code = pd_responses["choices"][0]["text"]
            col2.write(f"Executed query:")
            col2.code(exec_code)
            cursor.execute(exec_code)
            for row in cursor:
                st.write(row)

            # exec(exec_code)
            # st.write(results_df)

            output_prompt = f'Use the following pandas dataframe to answer the question in natural language. Today is {today}"""\n\n\n pandas dataframe: {dispatch_df}, question: {json_response["Original Request"]}"""\n'

            if json_response["Request Type"] == "Query":
                output_responses = openai.Completion.create(
                    model="text-davinci-003",
                    prompt=output_prompt,
                    temperature=0,
                    max_tokens=1024,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0,
                    stop=["Q:"],
                    timeout=20,
                )
                col1.text_area("Query results", output_responses["choices"][0]["text"])
                
        if json_response["Request Type"] == "Modify":
            prompt = f'Modify the pandas dataframe named df according to the request: \n """\n\n\n Request: {original_prompt}, Dataframe columns: {df_columns} """\n'

            pd_responses = openai.Completion.create(
                model="text-davinci-003",
                prompt=prompt,
                temperature=0,
                max_tokens=1024,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                stop=["Q:"],
                timeout=20,
            )

            exec_code = pd_responses["choices"][0]["text"]
            st.write(f"Executed query: {exec_code}")
            exec(exec_code)
            col2.write(df)
