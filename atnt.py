import streamlit as st
from streamlit_chat import message
import os
import openai
from pathlib import Path
from io import StringIO
import imageio as iio
from streamlit_extras.app_logo import add_logo
from datetime import date
import pandas as pd

openai.api_key = os.getenv('OPENAI_API_KEY')


st.set_page_config(
    page_title="AT&T sales lead script generator",
    page_icon=":robot:"
)

st.markdown("# AT&T Sales Lead Script Generator")


img = iio.imread('./assets/AT&T_logo_2016.svg.png')
st.sidebar.image(image=img, width=200)
st.sidebar.markdown("### Client Information")
profiles = pd.read_csv('./assets/b2b_profiles.csv')
profiles['combined'] = profiles[profiles.columns[0:2]].apply(
    lambda x: ' '.join(x.astype(str)),
    axis=1)

combined_name_list = profiles.loc[:, ['combined']].values.flatten().tolist()

profile_selection = st.sidebar.selectbox('Select Account', combined_name_list)

print(profile_selection)

row_idx = profiles.index[profiles['combined'] == profile_selection]
row = profiles.iloc[row_idx]
print(row.iloc[0])


first_name = st.sidebar.text_input('Profile First name', row.iloc[0]['First Name'])
last_name = st.sidebar.text_input('Profile Last name', row.iloc[0]['Last Name'])
position = st.sidebar.text_input('Profile position', row.iloc[0]['Position'])
company = st.sidebar.text_input('Company' , row.iloc[0]['Company'])
company_size = st.sidebar.text_input('Company Size', row.iloc[0]['Company size'])
spend = st.sidebar.text_input('Spend Last Month', row.iloc[0]['Spend last month'])
# add_logo("./assets/AT&T_logo_2016.svg.png")
col1, col2 = st.columns(2)

with col1:
    st.markdown("### Sales Information")
    current_product = st.multiselect('Current products', ['BB','Cradlepoint','SASE'])
    sales_play = st.selectbox('Sales Play', (['Account Acquisition','Upsell', 'Cross-sell', 'Retain']))
    likely_product_needs = st.multiselect(
    'Likely Product Needs',
    ['BB', 'SASE', 'Cradlepoint'],
    ['BB', 'SASE'])
    promotions = st.multiselect("Applicable Promotions",['Free Cradlepoint', '50% off SASE', '50% off retention', '50% off BB'])
    

with col2:
    st.markdown("### Model Parameter")
    email_length = st.slider(label='Email Length',min_value=128, max_value=1024, step=1, value=256)
    temperature = st.slider(label='Model temperature',min_value=0.0, max_value=1.0, step=0.01, value=0.5)
    tone = st.multiselect('Tone',['Professional','Engaging','Humours','Persuasive','Inspirational'], ['Professional','Engaging'])
    n = st.number_input(label='Number of candidate emails to generate',min_value=1)

   

openAI_prompt = f'Write a AT&T sales lead email with the following information: Salesperson name: Maria Hernandez Client name: {first_name} {last_name}, Client Company: {company}, Sales play: {sales_play}, Likely product needs: {likely_product_needs}, Applicable promotion: {promotions}. The tone of the email should be {tone}'

if st.button('Generate content'):
    with st.container():
        
        responses = openai.Completion.create(
            model="text-davinci-003",
            prompt=openAI_prompt,
            temperature=temperature,
            max_tokens=email_length,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=["Q:"],
            n=n,
            timeout=20)
        #print((list(range(0,1)))
        num_lis = list(range(1,n+1))
        
        str_lis = list(map(str, num_lis))
        print(str_lis)
        str_lis = [ f'Candidate Email {num}' for num in str_lis]
            
        tabs = st.tabs(str_lis)
        print(tabs)
        for i in range(0,n):
            response_text = responses["choices"][i-1]["text"]
            tabs[i-1].write(response_text)