import geopandas as gpd
import folium
from streamlit_folium import st_folium
import streamlit as st
import openai
import os
import pandas as pd
input_text = st.text_input("Enter Query here: ", value='', help='Try something like "Get all IPhone devices"')

openai.api_key = os.getenv("OPENAI_API_KEY")

foot_traffic = pd.read_csv('./assets/foot_traffic_sample.csv')
foot_traffic = gpd.GeoDataFrame(
    foot_traffic, geometry=gpd.points_from_xy(foot_traffic.longitude, foot_traffic.latitude))
foot_traffic = foot_traffic.set_crs('epsg:4326')

prompt = f"\"\"\"\npandas dataframe foot_traffic, foot_traffic= [ad_id,Date_,Hour_,latitude,longitude,Business_Location_Flag,Collection_Point_InMarket,id_type,Total_coverage_of_id,Total_pings_of_id,Indoor,BuildingID,TMOCustCnt,TMO_FIagIn,Building,Home_Flag,Category,Industry]\n without assigning new variable, {input_text}  \"\"\"\n\n\n"
print(f'Prompt: \n {prompt}')

m = folium.Map(location=[47.55481, -122.67772], tiles="OpenStreetMap", zoom_start=8)

if input_text != '':
    response = openai.Completion.create(
    model= "text-davinci-003",
    prompt = prompt,
    temperature=0.0,
    max_tokens=512,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0)
    response_text = response["choices"][0]["text"]
    response_text = response_text.replace('\n','')
    query_variable = 'filtered_df'
    
    print(f'response text {response_text}')
    exec_code = f'{query_variable}={response_text}'
    print(f'Executed code {exec_code}')
    
    exec(exec_code)
    print(filtered_df)
    
    heat_data = [[point.xy[1][0], point.xy[0][0]] for point in filtered_df.geometry]
    
    # for coord in heat_data:
    #     folium.Marker( location=[ coord[0], coord[1] ], fill_color='#43d9de', radius=2).add_to(m)

    #marker = folium.Marker(location=coord_data)
    #marker.add_to(m)
    
    
    folium.plugins.HeatMap(heat_data).add_to(m)
    
    
map_data = st_folium(m, key="fig1", width=1500)