import streamlit as st
import openai
import imageio as iio
import os
import json
import pandas as pd
from datetime import date
import pyodbc
from streamlit_toggle import toggle


def openAI_API(prompt):
    """openAI gpt API call, returns the top selection

    Args:
        prompt (_type_): _description_
    """
    print(prompt)
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
    response = responses["choices"][0]["text"]

    return response


def code_gen(db_format, ingestion_json):
    """Generate corresponding db queries

    Args:
        db_format (_type_): _description_
        ingestion_json (_type_): _description_

    Returns:
        _type_: _description_
    """

    if ingestion_json["Database"] == "Customer":

        prompt = f'Perform the request to the {db_format} database named customer_db. Today is {today}:\n """\n\n\n Request: {original_prompt}, Fields: {customer_columns} """\n'

    elif ingestion_json["Database"] == "Operations/Dispatch":
        prompt = f'Perform the request to the {db_format} database named dispatch_db. Today is {today}: \n """\n\n\n Request: {original_prompt}, Fields: {dispatch_columns} """\n'
    # st.write(prompt)
    show_query = openAI_API(prompt)
    # st.write(show_query)
    return show_query


openai.api_key = os.getenv("OPENAI_API_KEY")

# For OpenAI model to calculate days
today = date.today().strftime("%m/%d/%Y")

# Asset loading
st.set_page_config(page_title="Tigo B2B chatbot", page_icon=":robot:", layout="wide")
customer_df = pd.read_csv("./assets/b2b_profiles.csv")
dispatch_df = pd.read_csv("./assets/dispatch.csv")
cache_df = pd.read_csv("./assets/CRM_cache.csv")

# Logos
img = iio.imread("./assets/Logo_Tigo.svg.png")
st.sidebar.image(image=img, width=150)

img_business = iio.imread("./assets/tigo_logo.jpg")
st.image(image=img_business, width=300,use_column_width="auto")

# Example JSON
with open("./assets/query.json") as user_file:
    example_query = user_file.read()
with open("./assets/GDPR_query.json") as user_file:
    GDPR_example_query = user_file.read()

# customer dataframe column names
customer_columns = (
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

    # Database information
    st.header("Database parameter")
    with st.expander(label="See customer database"):
        st.dataframe(data=customer_df)
    customerDB_format = st.selectbox(
        label="Customer Database Format",
        options=["SQL", "NosQL", "Pandas", "MongoDB"],
        key="customerDB",
        index=2,
    )

    with st.expander(label="See dispatch database"):
        st.dataframe(data=dispatch_df)
    dispatchDB_format = st.selectbox(
        label="Dispatch Database Format",
        options=["SQL", "NoSQL", "Pandas", "MongoDB"],
        key="dispatchDB",
    )
    # Cache options
    st.header("System parameter")
    cache = toggle(label="Enable cache", key="cache",)
    # Regulation supervision
    st.header("Regulation parameter")
    cols1, cols2, cols3 = st.columns([1, 1, 1])
    with cols1:
        GDPR = toggle(label="GDPR compliance (Input)", key="GDPR",)
    with cols2:
        PII = toggle(label="PII Removal (Output)", key="PII",)
    with cols3:
        safeguard = toggle(label="DataBase Safeguard", key="safeguard",)

dispatch_df["Date"] = pd.to_datetime(dispatch_df["Date"])
customer_df["Contract end date"] = pd.to_datetime(customer_df["Contract end date"])
customer_df["Contract start date"] = pd.to_datetime(customer_df["Contract start date"])



# for row in cursor:
#     st.write(row)

col1, col2 = st.columns(2)

col1.header("User Interface")
col2.header("System Backend")

input_text = col1.text_input(
    "Input: ",
    value="",
    help='Try something like "What are the dispatches I have coming up in the next month?"',
)

cache_question_list = cache_df.Input.values.tolist()

# Pull from cache dataframe if question already in cache
if cache:
    if input_text in cache_question_list:
        row_idx = cache_df.index[cache_df["Input"] == input_text].tolist()[0]
        row = cache_df.iloc[[row_idx]]
        col2.write("Ingestion JSON: ")
        # col2.write(row)
        col2.code(row["Ingestion JSON"][row_idx], language="json")

        col2.write(f"Executed query")
        col2.code(row["Query code"][row_idx])

        col1.text_area(label="Query results", value=row["Query Results"][row_idx])
else:
        st.session_state.current_response = input_text
        # Ingestion call
        prompt = f'Based on the request, create a JSON file with the same structure as the example JSON file. Fill field with Unknown if you are unsure how to categorize the request. """\n\n\n Request: {input_text}, Example JSON: {example_query}. Possible values for Database Field: 1. Product, 2. Promotion, 3. Customer, 4. Policy, 5.Operations/Dispatch, 6.Unknown. Possible values for Request Type field: 1. Query, 2. Modify  """\n\n\n'

        if input_text:
            txt_response = openAI_API(prompt)
            ingestion_json = json.loads(txt_response)
            json.dumps(ingestion_json, indent=4)

            col2.write("Ingestion JSON: ")
            col2.code(txt_response, language="json")
            original_prompt = ingestion_json["Original Request"]

            if GDPR:
                # GDPR supervision at input level
                prompt = f'Check if the following request complies with GDPR (General Data Protection Regulation) and format the output the same way as the example JSON file \n """\n\n\n Request: {original_prompt}, example JSON: {GDPR_example_query} """\n'

                GDPR_compliance_txt = openAI_API(prompt)
                GDPR_compliance_JSON = json.loads(GDPR_compliance_txt)
                json.dumps(GDPR_compliance_JSON, indent=4)

                col1.write("GDPR Compliance")
                col1.code(GDPR_compliance_JSON["GDPR_compliance"])
                col1.text_area(
                    label="GDPR Comments:", value=GDPR_compliance_JSON["Explanation"]
                )

            if ingestion_json["Database"] == "Customer":
                if ingestion_json["Request Type"] == "Query":
                    prompt = f'Perform the request to the pandas dataframe named customer_df. Store results in a variable named results_df: \n """\n\n\n Request: {original_prompt}, Dataframe columns: {customer_columns} """\n'

                    exec_code = openAI_API(prompt)

                    col2.write(f"Executed query")

                    show_query = code_gen(
                        db_format=customerDB_format, ingestion_json=ingestion_json
                    )

                    col2.code(show_query)
                    exec(exec_code)

                    prompt = f'Use the following pandas dataframe to answer the question in natural language"""\n\n\n pandas dataframe: {results_df}, question: {ingestion_json["Original Request"]}"""\n'
                    # st.write(output_prompt)
                    if ingestion_json["Request Type"] == "Query":

                        output_query = openAI_API(prompt)
                        col1.text_area("Query results:", output_query)

                        if PII:  # If PII removal enabled, remove PII from output

                            prompt = f"Remove PII (Personal Identifiable Information) from the following statement '''\n\n\n statement: {output_query}''' \n "
                            PIIoutput_query = openAI_API(prompt)
                            col1.text_area(
                                "Query results (PII removed):", PIIoutput_query
                            )

                if ingestion_json["Request Type"] == "Modify":
                    prompt = f'Modify the pandas dataframe named customer_df according to the request: \n """\n\n\n Request: {original_prompt}, Dataframe columns: {customer_columns}"""\n'

                    exec_code = openAI_API(prompt)
                    col2.code(f"Executed query")
                    show_query = code_gen(
                        db_format=customerDB_format, ingestion_json=ingestion_json
                    )
                    col2.code(show_query)
                    exec(exec_code)
                    col1.write(customer_df)

            if (
                ingestion_json["Database"] == "Operations/Dispatch"
            ):  # Dispatch related questions

                if ingestion_json["Request Type"] == "Query":

                    prompt = f'Perform the request to the mySQL database named dispatch. Today is {today}: \n """\n\n\n Request: {original_prompt}, SQL fields: {dispatch_columns} """\n'
                    exec_code = openAI_API(prompt)
                    col2.write(f"System query:")
                    show_query = code_gen(
                        db_format=dispatchDB_format, ingestion_json=ingestion_json
                    )
                    col2.code(show_query)

                    cursor.execute(exec_code)
                    for row in cursor:
                        col2.write(row)

                    # exec(exec_code)
                    # st.write(results_df)

                    prompt = f'Use the following pandas dataframe to answer the question in natural language. Today is {today}"""\n\n\n pandas dataframe: {dispatch_df}, question: {ingestion_json["Original Request"]}"""\n'

                    if ingestion_json["Request Type"] == "Query":
                        query_results = openAI_API(prompt)
                        col1.text_area("Query results", query_results)

                if ingestion_json["Request Type"] == "Modify":
                    prompt = f'Perform the request to the mySQL database named dispatch. Today is {today}: \n """\n\n\n Request: {original_prompt}, SQL fields: {dispatch_columns} """\n'

                    exec_code = openAI_API(prompt)

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

                    col2.write(f"Executed query:")

                    show_query = code_gen(
                        db_format=dispatchDB_format, ingestion_json=ingestion_json
                    )

                    col2.code(show_query)

                    cursor.execute(exec_code)

                    for row in cursor:
                        st.write(row)
                    exec(exec_code)
                    col2.write(customer_df)
