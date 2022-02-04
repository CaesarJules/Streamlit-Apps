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

@st.cache
def convert_df(df):
    return df.to_csv(index = False).encode('utf-8')
@st.cache(show_spinner=False)
def get_results(dataset, url="http://127.0.0.1:8000/api/status/"):
    df = dataset.copy()
    spam_status = list()

    for i in range(len(df)):

        body_spam = {'review': str(df.iloc[i])}
        r2 = requests.post(url, data = body_spam) 
        spam_status.append(r2.json()["review_status"])
    
    df['status'] = np.array(spam_status)

    return df
    

def display_updated_layout(dataset, count_results, colors, c2, c3, fig):
    fig.update_layout(
        overwrite = True,
    )

    result = dict(dataset['status'].value_counts(sort=False))
    
    x = list(result.keys())
    y = list(result.values())

    if result['Real']>result['Spam']:
        c2.success("### Great ! the majority of reviews are real! &nbsp;😃")
    elif result['Spam']>result['Real']:
        c2.warning("### Oups, this is quite concerning! &nbsp;The majority of reviews are spam.&nbsp;😔")
    else:
        pass

    fig.add_trace(go.Pie(labels=x, values=y, pull=[0, 0.2], 
    marker_colors=['rgb(102, 255, 102)', 'rgb(255, 102, 102)']))
    c2.text("")
    c2.text("")
    c2.subheader("Multiple Reviews Analysis")
    c2.plotly_chart(fig, use_container_width=True)
    c2.subheader("Download the Spam Classification results file here:")
    
    csv = convert_df(dataset)
    c2.download_button(
        label="Download Results",
        data=csv,
        file_name='results.csv',
        mime='text/csv',
        key="download_id",
    )

    c3.subheader("Results header")
    c3.dataframe(data=dataset.head())
    c3.markdown("***")
    c3.subheader("Detailed Reviews Analysis")
    fig2 = go.Figure()

    fig2.update_layout(
        overwrite = True,
        width = 600,
    )
    fig2.add_trace(go.Bar(
        x=list(dict(count_results).values()),
        y=[str(elt) for elt in list(dict(count_results).keys())],
        orientation='h',
        text=[int(elt) for elt in list(dict(count_results).values())],
        textposition='auto',
        marker={"color": colors},
        )
    )
    c3.plotly_chart(fig2)


