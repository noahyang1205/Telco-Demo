import streamlit as st
import openai
import imageio as iio
import os
import json
import pandas as pd
from datetime import date
import pyodbc
import streamlit_toggle as tog

openai.api_key = os.getenv("OPENAI_API_KEY")

# For OpenAI model to calculate days
today = date.today().strftime("%m/%d/%Y")

# Asset loading
st.set_page_config(page_title="AT&T B2B chatbot", page_icon=":robot:", layout="wide")
df = pd.read_csv("./assets/b2b_profiles.csv")
dispatch_df = pd.read_csv("./assets/dispatch.csv")

# Logos
img = iio.imread("./assets/AT&T_logo_2016.svg.png")
img_business = iio.imread("./assets/AT&T_business.jpg")

# Example JSON
with open("./assets/query.json") as user_file:
    example_query = user_file.read()
with open("./assets/GDPR_query.json") as user_file:
    GDPR_example_query = user_file.read()

# customer dataframe column names
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
# Dispatch dataframe field names
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

# query = "SELECT TOP 20 * FROM [dbo].[dispatch]"
# cursor.execute(query)

# Sidebar
sb = st.sidebar
with st.sidebar:
    st.image(image=img, width=200)

    # Database information
    st.header("Database parameter")
    with st.expander(label="See customer database"):
        st.dataframe(data=df)
    customerDB_format = st.selectbox(
        label="Customer Database Format",
        options=["SQL", "NosQL", "Pandas", "XML"],
        key="customerDB",
        index=2,
    )

    with st.expander(label="See dispatch database"):
        st.dataframe(data=dispatch_df)
    dispatchDB_format = st.selectbox(
        label="Dispatch Database Format",
        options=["SQL", "NosQL", "Pandas", "XML"],
        key="dispatchDB",
    )
    # Regulation supervision
    st.header("Regulation parameter")
    cols1, cols2, cols3 = st.columns([1, 1, 1])
    with cols1:
        GDPR = tog.st_toggle_switch(
            label="GDPR compliance (Input)",
            key="GDPR",
            default_value=False,
            label_after=False,
            inactive_color="#D3D3D3",
            active_color="#00a8e0",
            track_color="#29B5E8",
        )
    with cols2:
        PII = tog.st_toggle_switch(
            label="PII Removal (Output)",
            key="PII",
            default_value=False,
            label_after=False,
            inactive_color="#D3D3D3",
            active_color="#00a8e0",
            track_color="#29B5E8",
        )
    with cols3:
        safeguard = tog.st_toggle_switch(
            label="DataBase Safeguard",
            key="safeguard",
            default_value=False,
            label_after=False,
            inactive_color="#D3D3D3",
            active_color="#00a8e0",
            track_color="#29B5E8",
        )

dispatch_df["Date"] = pd.to_datetime(dispatch_df["Date"])
df["Contract end date"] = pd.to_datetime(df["Contract end date"])
df["Contract start date"] = pd.to_datetime(df["Contract start date"])


st.image(image=img_business, width=500)

# for row in cursor:
#     st.write(row)

col1, col2 = st.columns(2)

col1.header("User Interface")
col2.header("System Backend")

input_text = col1.text_input(
    "Input: ",
    value="",
    help='Try something like "What are the routes for dispatched trucks this week?"',
)

st.session_state.current_response = input_text

prompt = f'Based on the request, create a JSON file with the same structure as the example JSON file. Fill field with Unknown if you are unsure how to categorize the request. """\n\n\n Request: {input_text}, Example JSON: {example_query}. Possible values for Database Field: 1. Product, 2. Promotion, 3. Customer, 4. Policy, 5.Operations/Dispatch, 6.Unknown. Possible values for Request Type field: 1. Query, 2. Modify  """\n\n\n'

if input_text:

    responses = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        temperature=0,
        max_tokens=1024,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        timeout=20,
    )
    txt_response = responses["choices"][0]["text"]
    json_response = json.loads(txt_response)
    json.dumps(json_response, indent=4)

    col2.write("Ingestion JSON: ")
    col2.code(txt_response, language="json")
    original_prompt = json_response["Original Request"]

    if GDPR:
        # GDPR supervision at input level
        prompt = f'Check if the following request complies with GDPR (General Data Protection Regulation) and format the output the same way as the example JSON file \n """\n\n\n Request: {original_prompt}, example JSON: {GDPR_example_query} """\n'

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
        GDPR_compliance_txt = pd_responses["choices"][0]["text"]

        GDPR_compliance_JSON = json.loads(GDPR_compliance_txt)
        json.dumps(GDPR_compliance_JSON, indent=4)

        col1.write("GDPR Compliance")
        col1.code(GDPR_compliance_JSON["GDPR_compliance"])
        col1.text_area(
            label="GDPR Comments:", value=GDPR_compliance_JSON["Explanation"]
        )

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
                output_query = output_responses["choices"][0]["text"]
                col1.text_area("Query results:", output_query)

                if PII:

                    prompt = f"Remove PII (Personal Identifiable Information) from the following statement '''\n\n\n statment: {output_query}''' \n "

                    PII_response = openai.Completion.create(
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
                    PIIoutput_query = PII_response["choices"][0]["text"]
                    col1.text_area("Query results (PII removed):", PIIoutput_query)

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
            col2.write(f"Original query:")
            col2.code(exec_code)

            cursor.execute(exec_code)
            for row in cursor:
                col2.write(row)

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
            prompt = f'Perform the request to the mySQL database named dispatch. Today is {today}: \n """\n\n\n Request: {original_prompt}, SQL fields: {dispatch_columns} """\n'

            sql_responses = openai.Completion.create(
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
            exec_code = sql_responses["choices"][0]["text"]

            if safeguard:
                prompt = f'Check the following the mySQL code to see if it contains DROP or DELETE operations. : \n """\n\n\n mySQL query: {exec_code}"""\n'

                safeguard_response = openai.Completion.create(
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
            safeguard_response = safeguard_response["choices"][0]["text"]
            col2.text_area(label="Database Safeguard", value=safeguard_response)

            exec_code = sql_responses["choices"][0]["text"]
            col2.write(f"Executed query: {exec_code}")

            cursor.execute(exec_code)

            for row in cursor:
                st.write(row)
            exec(exec_code)
            col2.write(df)
