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

tahun_min = int(data["year"].min())
tahun_max = int(data["year"].max())
rentang = st.slider("Rentang Tahun", min_value=tahun_min, max_value=tahun_max, value=(tahun_min, tahun_max))
awal, akhir = rentang
data_filter = data[(data["year"] >= awal) & (data["year"] <= akhir)]

kolom_indikator = [col for col in data.columns if col != "year"]
kolom_layout = st.columns(4)

for i, ind in enumerate(kolom_indikator[:4]):
    data_bersih = data_filter[ind].dropna()
    nilai_terbaru = data_bersih.iloc[-1]
    nilai_sebelumnya = data_bersih.iloc[-2]

    if len(data_bersih) >= 2:

        delta = nilai_terbaru - nilai_sebelumnya
    
        kolom_layout[i].metric(
            label=ind, 
            value=round(nilai_terbaru, 2), 
            delta=round(delta, 2)
        )
    else:

        kolom_layout[i].metric(
            label=ind,
            value=round(nilai_terbaru, 2)
        )

indikator = st.selectbox("Pilih Indikator:", kolom_indikator)

fig = px.line(data_filter, x="year", y=indikator)
st.plotly_chart(fig, use_container_width=True)
