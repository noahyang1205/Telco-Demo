import geopandas as gpd
import folium
from streamlit_folium import st_folium
import streamlit as st
import openai
import os
import pandas as pd

st.set_page_config(layout="wide")
if 'past_response' not in st.session_state:
    st.session_state.past_response = ''
if 'current_response' not in st.session_state:
    st.session_state.current_response = ''
if 'plot_data ' not in st.session_state:
    st.session_state.plot_data = ''
if 'exec_code ' not in st.session_state:
    st.session_state.exec_code = ''
input_text = st.text_input("Enter Query here: ", value='', help='Try something like "Get all IPhone and Home devices"')
st.session_state.current_response = input_text


openai.api_key = os.getenv("OPENAI_API_KEY")

foot_traffic = pd.read_csv('./assets/foot_traffic_sample.csv')
foot_traffic = gpd.GeoDataFrame(
    foot_traffic, geometry=gpd.points_from_xy(foot_traffic.longitude, foot_traffic.latitude))
foot_traffic = foot_traffic.set_crs('epsg:4326')

prompt = f"\"\"\"\npandas dataframe foot_traffic, foot_traffic= [ad_id,Date_,Hour_,latitude,longitude,Business_Location_Flag,Collection_Point_InMarket,id_type,Total_coverage_of_id,Total_pings_of_id,Indoor,BuildingID,TMOCustCnt,TMO_FIagIn,Building,Home,Category,Industry]\n without assigning new variable, {input_text}  \"\"\"\n\n\n"
#print(f'Prompt: \n {prompt}')

if 'm' not in st.session_state:
    st.session_state.m = folium.Map(location=[47.55481, -122.67772], tiles="OpenStreetMap", zoom_start=8)

if st.session_state.current_response != '' and (st.session_state.current_response!= st.session_state.past_response):
    # Only make a query when current response is not empty and not quired already
    print(f'current {st.session_state.current_response}, past {st.session_state.past_response}')
    response = openai.Completion.create(
    model= "text-davinci-003",
    prompt = prompt,
    temperature=0.0,
    max_tokens=512,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0,
    timeout=200)
    
    st.session_state.past_response = st.session_state.current_response # update past response after query
    
    response_text = response["choices"][0]["text"]
    response_text = response_text.replace('\n','')
    query_variable = 'filtered_df'
    
    #print(f'response text {response_text}')
    exec_code = f'{query_variable}={response_text}'
    print(f'Requesting Query as: {exec_code}')
    st.session_state.exec_code = exec_code
    exec(exec_code)
    #print(filtered_df)
    
    st.session_state.plot_data = [[point.xy[1][0], point.xy[0][0]] for point in filtered_df.geometry]
    #print(st.session_state.plot_data)
    # for coord in heat_data:
    #     folium.Marker( location=[ coord[0], coord[1] ], fill_color='#43d9de', radius=2).add_to(m)

    #marker = folium.Marker(location=coord_data)
    #marker.add_to(m)
    #st.write(f"Query executed is: {exec_code}")
    
    
    
    folium.plugins.HeatMap(st.session_state.plot_data).add_to(st.session_state.m)
if st.session_state.exec_code != '':
        st.sidebar.write(f"Query executed is: {st.session_state.exec_code}")
map_data = st_folium(st.session_state.m, key="fig1", width=1500)



