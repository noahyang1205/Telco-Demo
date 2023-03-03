import streamlit as st
import os
import openai
import imageio as iio

st.set_page_config(
    page_title="Ad Generation Demo",
    page_icon=":robot:"
)

openai.api_key = os.getenv('OPENAI_API_KEY')

st.header("Ad Generation Demo")

img = iio.imread('./assets/logo.png')
st.sidebar.image(image=img)

prompt = st.text_input("Enter Image prompt", "cute dog")

#prompt = "people having fun"
response = openai.Image.create(
  prompt=prompt,
  n=1,
  size="512x512"
)
image_url = response['data'][0]['url']

st.markdown(f"![{prompt}]({image_url})")
st.write(prompt)