import streamlit as st
import requests
import pandas as pd
import plotly.express as px

API_URL = "http://localhost:8000"

LABEL_ID = {
    "gdp_growth":   "Pertumbuhan PDB (%)",
    "inflation":    "Inflasi IHK (%)",
    "unemployment": "Pengangguran (%)",
    "poverty":      "Kemiskinan (%)",
}

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


    if len(data_bersih) >= 2:

        nilai_sebelumnya = data_bersih.iloc[-2]
        delta = nilai_terbaru - nilai_sebelumnya
        

        kolom_layout[i].metric(
            label=LABEL_ID[ind], 
            value=f"{nilai_terbaru:.2f}%", 
            delta=f"{delta:.2f}%"
        )
    else:

        kolom_layout[i].metric(
            label=LABEL_ID[ind],
            value=f"{nilai_terbaru:.2f}%"
        )

daftar_pilihan = [LABEL_ID[col] for col in kolom_indikator]

pilihan_label = st.selectbox("Pilih Indikator:", daftar_pilihan)

indikator_asli = None

for k, v in LABEL_ID.items():
    if v == pilihan_label:
        indikator_asli = k
        break

fig = px.line(data_filter, x="year", y=indikator_asli, markers=True)
fig = fig.update_layout(title=f"Tren {pilihan_label} - Indonesia")
st.caption("Sumber: World Bank (via API) • update berkala")
st.plotly_chart(fig, use_container_width=True)
