import streamlit as st
import pandas as pd
import numpy as np
import requests
from plotly.offline import iplot
import plotly.graph_objs as go
import plotly.express as px
from pandas.io.json import json_normalize
from streamlit.script_runner import RerunException, StopException
import time
import os
import matplotlib.pyplot as plt
from functions import *

#Get the current file's directory
path = os.path.dirname(__file__)
filepath = os.path.join(path, 'data/sample_webapp_test.csv')
logo = os.path.join(path, 'data/logo.png')
st.set_page_config(page_title='Reviews Pundit', page_icon = logo, layout = 'wide', initial_sidebar_state = 'auto')

fig = go.Figure()
st.title("Reviews Pundit")
st.text("")
st.text("")
st.text("")
#---------------------------------#
# About
expander_bar = st.expander("About")
expander_bar.markdown("""
##### This app analyzes the *sentiment* expressed in input reviews and filter *spams*!
* **EDA and Model Development Details:** [CoinMarketCap](http://coinmarketcap.com).
* **Sample dataset source:** [CoinMarketCap](http://coinmarketcap.com).
* **Python libraries used:** streamlit, pandas, numpy, requests, plotly, time, os, matplotlib.
""")

st.set_option('deprecation.showfileUploaderEncoding', False)

st.text("")
st.text("")

col2, col3 = st.columns((2,1))

sample = col2.empty()
sample.selectbox(label = "", options=["", "Amazon PC reviews sample"], key="sample_id")
txt_input = False
if st.session_state["sample_id"]!="":
    txt_input = True
st.sidebar.write("# Customer Product Review(s)")
st.sidebar.text("")
st.sidebar.text("")
with st.sidebar:
    with st.form("myform", clear_on_submit=True):
        single_review = st.text_area(label="Please enter below a product review:", key="txt_id", disabled=txt_input)
        st.write("# Or")
        uploaded_file = st.file_uploader(label="Upload your input reviews CSV file", key="fl_id",
        type=["csv"])
        st.warning("Note: Products reviews must be stored in a column called *review*")       
        submit = st.form_submit_button(label="Submit")
    if submit:
        temp = st.empty()
        if uploaded_file!=None:
            valid_data = "review" in list(pd.read_csv(uploaded_file, nrows=0).columns)
            if valid_data == False:
                temp.error('There must be a review column in your dataset!')
                time.sleep(1)
                del st.session_state["fl_id"]
                del st.session_state["txt_id"]
                del st.session_state["sample_id"]
                raise RerunException(st.script_request_queue.RerunData(None))
            else:
                temp.success('Submitted')
        elif len(single_review.strip()) > 0:
            sample.empty()
            temp.success('Submitted')   
        else:
            temp.error('You must have at least one review!')
        time.sleep(1)
        temp.empty()

st.sidebar.markdown("***")

if st.sidebar.button('Refresh Page'):
    del st.session_state["txt_id"]
    del st.session_state["fl_id"]
    del st.session_state["sample_id"]
        
    raise RerunException(st.script_request_queue.RerunData(None))

if uploaded_file != None or st.session_state["sample_id"]!="":
    #my_bar = st.progress(0)
    filter_spam = col3.checkbox('Filter out Spam Reviews')
    input_df = pd.DataFrame()
    with st.spinner('Fetching Results ...'):
        if uploaded_file != None:
            uploaded_file.seek(0)    
            input_df = pd.read_csv(uploaded_file, nrows=50, low_memory=False)
            uploaded_data = get_results(input_df)
            data = pd.DataFrame(uploaded_data)

        
        elif st.session_state["sample_id"] != "":
            input_df = pd.read_csv(filepath, nrows=50, low_memory=False)
            sample_data = get_results(input_df)
            data = pd.DataFrame(sample_data)
        else:
            pass

        sample.empty()
        df = pd.DataFrame(data)
        total_result = df[["status", "sentiment", "verified"]].value_counts(sort=False)
 
    
        if filter_spam == False:
            colors = total_result.to_frame().reset_index().status.map({"Real":'rgb(153, 255, 153)',"Spam":'rgb(255, 153, 153)'}).to_list()
            display_updated_layout(df, total_result, colors, col2, col3, fig)
                    
        elif filter_spam == True:
            df = df[df['status']=="Real"].reset_index(drop=True)
            colors = ['rgb(153, 255, 153)']*len(df)
            display_updated_layout(df, total_result["Real"], colors, col2, col3, fig)
                    
        else:
            pass
    
    
elif len(single_review.strip())>0:
    sample.empty()
    url = "http://127.0.0.1:8000/api/status/"
    body = {'text': single_review}

    r = requests.post(url, data = body)
    result = r.json()["text_sentiment"]

    if result=="Positive":
        st.success("## Great Work there! You got a Positive Review &nbsp;😃")
    elif result=="Negative":
        st.warning("## Try improving your product! You got a Negative Review  &nbsp;😔")
    else:
        pass
    
else:
    col2.subheader(" ⬅ Please enter product reviews, or use one of the sample dataset(s) proposed above.")

    


