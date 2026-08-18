import streamlit as st
import requests
import pandas as pd
import plotly.express as px

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Dashboard World Bank", layout="wide")
st.title("Visualisasi Dashboard World Bank")

@st.cache_data(ttl=3600)
def fetch_data():
    response = requests.get(f"{API_URL}/indicators", params={"start_year": 2000})
    response.raise_for_status()
    return pd.DataFrame(response.json())

data = fetch_data()

kolom_indikator = [col for col in data.columns if col != "year"]

indikator = st.selectbox("Pilih Indikator:", kolom_indikator)

fig = px.line(data, x="year", y=indikator)
st.plotly_chart(fig, use_container_width=True)