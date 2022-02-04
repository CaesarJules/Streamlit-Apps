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

#Get the current file's directory
path = os.path.dirname(__file__)
#Create cache's filepath
filepath = os.path.join(path, 'data/cache_final.p')

def get_dates_till_today(start_date):
  return pd.date_range(end=datetime.datetime.today(), start=start_date).strftime('%Y-%m-%d').tolist()

def get_region_report(region_name, date, df):
  url = "https://covid-19-statistics.p.rapidapi.com"
  headers = {
      'x-rapidapi-host': 'covid-19-statistics.p.rapidapi.com',
      'x-rapidapi-key': '44e824ba26mshbd88513db1a43d3p174f66jsn2f60602ce307'
    }
  #Get countries names and iso
  response = requests.request(method="GET", url=f"{url}/reports", 
              params={'iso': df.loc[df.name == region_name, 'iso'], 
                'region_name': region_name, 'date': date}, headers=headers)
  response_json = json.loads(response.text)

  if len(response_json) > 0 and 'data' in response_json:
    return response_json['data']

  return []

def get_worldwide_data(date):
    url = "https://covid-19-statistics.p.rapidapi.com"
    headers = {
        'x-rapidapi-host': 'covid-19-statistics.p.rapidapi.com',
        'x-rapidapi-key': '44e824ba26mshbd88513db1a43d3p174f66jsn2f60602ce307'
    }
    #Get countries names and iso
    response = requests.request(method="GET", url=f"{url}/reports/total",params={'date':date}, headers=headers)
    #json.loads(response.text)['data']
    response_json = json.loads(response.text)

    if len(response_json) > 0 and 'data' in response_json:
      return response_json['data']

    return []
@st.cache(show_spinner=False)
def get_latest_worldwide_data():
    url = "https://covid-19-statistics.p.rapidapi.com"
    headers = {
        'x-rapidapi-host': 'covid-19-statistics.p.rapidapi.com',
        'x-rapidapi-key': '44e824ba26mshbd88513db1a43d3p174f66jsn2f60602ce307'
    }
    #Get countries names and iso
    response = requests.request(method="GET", url=f"{url}/reports/total", headers=headers)
    #json.loads(response.text)['data']
    response_json = json.loads(response.text)

    if len(response_json) > 0 and 'data' in response_json:
      return response_json['data']

    return []

def get_countries_data(dates, regions, df_regions):
  temp = defaultdict(list)
  result = defaultdict(dict)
  for region in regions:
    for date in dates:
      sol = {'confirmed_diff':0, 'deaths_diff':0, 'date':date}
      data = get_region_report(region, date, df_regions)
      if len(data)> 0:
        for report in data:
          sol['confirmed_diff'] += report['confirmed_diff']
          sol['deaths_diff'] += report['deaths_diff']
      temp[region].append(sol)

  for region in regions:
    result[region]['confirmed_diff'] = np.array([sub['confirmed_diff'] for sub in temp[region]])
    result[region]['deaths_diff'] = np.array([sub['deaths_diff'] for sub in temp[region]])
  result['dates'] = np.array(dates)

  #Get global data and append it to the result
  glob_data = defaultdict(list)
  for date in dates:
    data = get_worldwide_data(date)
    if len(data)>0:
      glob_data['global_conf_diff'].append(data['confirmed_diff'])
      glob_data['global_deaths_diff'].append(data['deaths_diff'])

  result['global_conf_diff'] = np.array(glob_data['global_conf_diff'])
  result['global_deaths_diff'] = np.array(glob_data['global_deaths_diff'])

  return result
@st.cache(show_spinner=False)
def get_latest_weekly_data(data, regions, n_weeks):
  sol = {'conf_per_rgn': np.array([np.sum(data[rgn]['confirmed_diff'][-(7*n_weeks):]) for rgn in regions]), 'deaths_per_rgn': np.array([np.sum(data[rgn]['deaths_diff'][-(7*n_weeks):]) for rgn in regions])}
  return sol

def get_optimized_regions_data(data, regions):
  result = data.copy()
  #Get new cases globally and per region
  #New cases equals to the average of confirmed cases over the last 7 days
  result['global_new_cases'] = np.array([np.mean(result['global_conf_diff'][-8:-1]), 
  np.mean(result['global_conf_diff'][-7:])])
  result['new_cases_per_rgn'] = {k:np.mean(result[k]['confirmed_diff'][-7:]) for k in regions}
  result['top5_rgn_new_cases'] = sorted(result['new_cases_per_rgn'].items(), key=lambda x: x[1], reverse=True)[:5]

  #Get the data for the latest 1 to 5 weeks
  for i in range(1,6):
    result[f"top{i}_wk"] = get_latest_weekly_data(result, regions, i)
  
  return result.copy()

def update_cached_data(data, new_data, regions):
  old_data = dict(data)
  for rgn in regions:
    old_data[rgn]['confirmed_diff'] = np.append(old_data[rgn]['confirmed_diff'][:-1], 
    new_data[rgn]['confirmed_diff'])
    old_data[rgn]['deaths_diff'] = np.append(old_data[rgn]['deaths_diff'][:-1], 
    new_data[rgn]['deaths_diff'])

  old_data['dates'] = np.append(old_data['dates'][:-1], new_data['dates'])
  old_data['global_conf_diff'] = np.append(old_data['global_conf_diff'][:-1], new_data['global_conf_diff'])
  old_data['global_deaths_diff'] = np.append(old_data['global_deaths_diff'][:-1], 
  new_data['global_deaths_diff'])

  return old_data.copy()

def cache_data(data, latest_date, regions, df_regions):
    time1 = datetime.datetime.strptime(datetime.datetime.now(timezone('Canada/Eastern')).strftime('%Y-%m-%d'), '%Y-%m-%d')
    if time1 > (latest_date + datetime.timedelta(days=1)):
        new_dates = get_dates_till_today(latest_date)
        #Remove today's date from the dates to be cached
        new_dates.pop(-1)
        if len(new_dates)>0:
            new_data = get_countries_data(new_dates, regions, df_regions)
            #Update the data

            temp = update_cached_data(data, new_data, regions)
            data = get_optimized_regions_data(temp, regions)
            #Cache the new data
            with open(filepath, 'wb') as fp:
                pickle.dump(data, fp, protocol=pickle.HIGHEST_PROTOCOL)
    
    return data