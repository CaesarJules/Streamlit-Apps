import streamlit as st
import pandas as pd
import numpy as np
import requests
from plotly.offline import iplot
import plotly.graph_objs as go
import plotly.express as px
import json 
import datetime
from collections import defaultdict
import pickle5
import pickle
import os
import warnings
from IPython.display import Markdown as md
from pytz import timezone
from copy import deepcopy
from streamlit.script_runner import RerunException, StopException
from functions import *

#Get the current file's directory
path = os.path.dirname(__file__)
#Create cache's filepath
filepath = os.path.join(path, 'data/cache_final.p')
#Create logo filepath
logo = os.path.join(path, 'data/logo.png')

st.set_page_config(page_title='COVID-19 Dashboard', page_icon = logo, layout = 'wide', initial_sidebar_state = 'auto')

fig = go.Figure()
fig2 = go.Figure()
fig2_title=f""" """
fig3 = go.Figure()
fig3_title=f""" """

#st.markdown("<h1 style='text-align: justified;'>Covid19 Dashboard</h1>", unsafe_allow_html=True)
st.title("COVID19 Statistics")
# About
expander_bar = st.expander("About")
expander_bar.markdown("""
#### This is a COVID-19 statistics Dashboard Based on public data by Johns Hopkins CSSE.
* **EDA and App Development Details:** [CoinMarketCap](http://coinmarketcap.com).
* **API Credits:** [CoinMarketCap](http://coinmarketcap.com).
* **Python libraries used:** streamlit, pandas, numpy, requests, plotly, time, os, matplotlib, collections, datetime, IPython.
""")
#Initialize the starting date in our data
initial_date = datetime.datetime.today()
dates = get_dates_till_today(initial_date)

@st.cache(show_spinner=False)
def get_regions_list():
    url = "https://covid-19-statistics.p.rapidapi.com"
    headers = {
        'x-rapidapi-host': 'covid-19-statistics.p.rapidapi.com',
        'x-rapidapi-key': '96a36f8da6msh9ee894aabc7ae5bp196263jsn8dfae3d97a64'
    }
    #Get countries names and iso
    response = requests.request(method="GET", url=f"{url}/regions", headers=headers)
    #json.loads(response.text)['data']
    response_json = json.loads(response.text)['data']

    return pd.json_normalize(response_json)

df_regions = get_regions_list()
df_regions = df_regions.sort_values('name').reset_index(drop=True)
regions = list(df_regions.name)
#Clean the list of regions
regions = [x for x in regions if x not in ['Others','Cruise Ship']]
iso = [df_regions.loc[df_regions.name==rgn, 'iso'].values[0] for rgn in regions]

def load_cache(filepath=filepath):
    #Check first if there is a cached file and if it can be accessed
    if os.path.isfile(filepath) and os.access(filepath, os.R_OK):
        with open(filepath, 'rb') as fp:
            return pickle5.load(fp)
    else:
        return {}

cached_data = load_cache()

#Use the first date in the data to cache all data
latest_cache_date = initial_date
data = dict()

if len(cached_data)>0:
    #Get the latest cache date
    data = dict(cached_data)
    temp = data['dates'][-1]
    latest_cache_date = datetime.datetime.strptime(temp, '%Y-%m-%d')
    #Update the initial date to the first date in our cached data
    initial_date = data['dates'][0]
    initial_date = datetime.datetime.strptime(initial_date, '%Y-%m-%d')
    dates = get_dates_till_today(initial_date)
    #Update cached data 
    with st.spinner('Fetching results ....'):
        data = cache_data(data, latest_cache_date, regions, df_regions)
        
else:
    print("Error, No cache found!!!")

with st.spinner('Fetching results ....'):
    #Create and populate the sidebar
    latest_ww = get_latest_worldwide_data()
    latest_update = datetime.datetime.strptime(latest_ww['last_update'], 
    '%Y-%m-%d %H:%M:%S').strftime('%B %d, %Y at %I:%M %p')
    st.sidebar.markdown(f"""<p style="font-size:22px;">
                            Total Confirmed Cases:<br>
                            <span style="color: #FF0000 ;text-align: justify ;font-weight:bold; ">{latest_ww["confirmed"]:,}</span><br>
                            Total Deaths :<br>
                            <span style="color: #B8860B ; text-align: justify ;font-weight:bold; ">{latest_ww["deaths"]:,}</span> <br>
                            <span style="font-size:20px; color: #778899 ">
                            Last Updated on: <br>
                            {latest_update}</span>
                            </p>
                            """, unsafe_allow_html=True
                        )

    st.sidebar.markdown("***")
    st.sidebar.header('Filter your search')
    graph_type = st.sidebar.selectbox(label="Cases type",options=['confirmed','deaths','new_cases'], key="gtype_id")
    st.sidebar.subheader('Search by country or region 📍')
    countries_selected = st.sidebar.multiselect(label="Country", options=regions, key="rgns_id")
    if graph_type!='new_cases':
        num_weeks_selected = st.sidebar.slider(label="Number of weeks to display", min_value=1, max_value=5, value=3, key="wk_num_id")

    #Plot the world heat map
    #Use the selected graph_type

    st.markdown(f"""<h4 style='text-align: justify;'>Number of COVID-19 cases worldwide on {latest_cache_date.strftime('%A %B %d, %Y')}</h4>""", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("Confirmed cases", f"{data['global_conf_diff'][-1]:,}", 
    f"{round((data['global_conf_diff'][-1] - data['global_conf_diff'][-2])/data['global_conf_diff'][-2], 2)}%")

    col2.metric("Deaths", f"{data['global_deaths_diff'][-1]:,}", 
    f"{round((data['global_deaths_diff'][-1] - data['global_deaths_diff'][-2])/data['global_deaths_diff'][-2], 2)}%")

    col3.metric("New cases", f"{int(data['global_new_cases'][-1]):,}", 
    f"{round((data['global_new_cases'][-1] - data['global_new_cases'][-2])/data['global_new_cases'][-2], 2)}%")

    map_subtitle = "COVID-19 new cases worldwide (latest week average)"
    if graph_type!='new_cases':
        map_subtitle = f"COVID-19 {graph_type} cases for the last {num_weeks_selected*7} days"

    fig.update_layout(
        geo=dict(
            showframe=False,
            showcoastlines=False,
            projection_type='equirectangular'
        ),
        overwrite = True,
        width=1200,
        height=800,
        annotations = [dict(
            x=0.55,
            y=0.15,
            xref='paper',
            yref='paper',
            text= map_subtitle,
            showarrow = False,
            font_color = 'black',
            font_size = 30
        )]
    )
    fig2.update_layout(
        overwrite = True,
        width=1100,
        height=600
    )
    fig3.update_layout(
        overwrite = True,
        width=1100,
        height=600
    )

    if graph_type=='new_cases':
        if len(countries_selected)>0:

            fig2_title = f"""<h4>Number of COVID-19 new cases  in {", ".join(countries_selected)} as of {latest_cache_date.strftime('%A %B %d, %Y')} (latest week average)</h4>"""

            fig2.add_trace(go.Bar(
                x=[data['new_cases_per_rgn'][x] for x in countries_selected],
                y=countries_selected,
                orientation='h',
                text=[int(data['new_cases_per_rgn'][x]) for x in countries_selected],
                textposition='auto'
                )
            )


        else:
            fig.add_trace(go.Choropleth(
            locations = iso,
            z = list(data['new_cases_per_rgn'].values()),
            text = regions,
            colorscale = 'YlOrBr',
            autocolorscale=False,
            marker_line_color='darkgray',
            marker_line_width=0.5,
            colorbar_title = "Number of cases",
            ))

            fig2.add_trace(go.Bar(
                x=[y for x,y in data['top5_rgn_new_cases']],
                y=[x for x,y in data['top5_rgn_new_cases']],
                orientation='h',
                text=[int(y) for x,y in data['top5_rgn_new_cases']],
                textposition='auto'
                )
            )
            fig2_title = f"""<h4>Top 5 countries with the highest number of COVID-19 new cases as of {latest_cache_date.strftime('%A %B %d, %Y')}</h4>"""

    else:
        global_case_keys = {'rgn':{
                                    'confirmed':'conf_per_rgn',
                                    'deaths':'deaths_per_rgn'
                                },
                            'glbl':{
                                    'confirmed':'global_conf_diff',
                                    'deaths':'global_deaths_diff'
                                },
                            'ctr':{
                                    'confirmed':'confirmed_diff',
                                    'deaths':'deaths_diff'
                                }
                            }

        if len(countries_selected)>0:

            fig2_title = f"""<h4>Number of COVID-19 <i>daily difference</i> {graph_type} cases in {", ".join(countries_selected)} for the last {num_weeks_selected*7} days</h4>"""

            fig3_title = f"""<h4>Number of COVID-19 <i>daily difference</i> {graph_type} cases in {", ".join(countries_selected)} since {datetime.datetime.strptime(data['dates'][0], "%Y-%m-%d").strftime('%A %B %d, %Y')}</h4>"""

            for x in countries_selected:
                fig2.add_trace(go.Scatter(
                    x=data['dates'][-(num_weeks_selected*7):], 
                    y=data[x][global_case_keys['ctr'][graph_type]][-(num_weeks_selected*7):],
                    mode='lines',
                    name=x
                    )
                )

                fig3.add_trace(go.Bar(
                    x=data['dates'], 
                    y=data[x][global_case_keys['ctr'][graph_type]],
                    name=x
                    )
                )


        
        else:
            fig.add_trace(go.Choropleth(
                locations = iso,
                z = data[f"top{num_weeks_selected}_wk"][global_case_keys['rgn'][graph_type]],
                text = regions,
                colorscale = 'YlOrBr',
                autocolorscale=False,
                marker_line_color='darkgray',
                marker_line_width=0.5,
                colorbar_title = "Number of cases",
            ))

            fig2.add_trace(go.Bar(
                x=data['dates'][-(num_weeks_selected*7):],
                y=data[global_case_keys['glbl'][graph_type]][-(num_weeks_selected*7):],
                )
            )
            fig2_title = f"""<h4>Number of COVID-19 <i>daily difference</i> {graph_type} cases worldwide over the last {num_weeks_selected*7} days</h4>"""

            fig3.add_trace(go.Scatter(
                x=data['dates'], 
                y=data[global_case_keys['glbl'][graph_type]],
                mode='lines+markers',
                name='lines+markers'
                )
            )
            fig3_title = f"""<h4>Number of COVID-19 <i>daily difference</i> {graph_type} cases worldwide since {datetime.datetime.strptime(data['dates'][0], "%Y-%m-%d").strftime('%A %B %d, %Y')}</h4>"""

    if len(countries_selected)<=0:
        st.plotly_chart(fig)
        st.markdown(fig2_title, unsafe_allow_html=True)
        st.plotly_chart(fig2)
        if graph_type!='new_cases':
            st.markdown(fig3_title, unsafe_allow_html=True)
            st.plotly_chart(fig3)
    else:
        st.markdown(fig2_title, unsafe_allow_html=True)
        st.plotly_chart(fig2)
        if graph_type!='new_cases':
            st.markdown(fig3_title, unsafe_allow_html=True)
            st.plotly_chart(fig3)

