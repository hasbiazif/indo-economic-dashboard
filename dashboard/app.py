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

# Slider

tahun_min = int(data["year"].min())
tahun_max = int(data["year"].max())
rentang = st.slider("Rentang Tahun", min_value=tahun_min, max_value=tahun_max, value=(tahun_min, tahun_max))
awal, akhir = rentang
data_filter = data[(data["year"] >= awal) & (data["year"] <= akhir)]

kolom_indikator = [col for col in data.columns if col != "year"]

# KPI
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

# TAB
tab_ringkasan, tab_semua = st.tabs(["Ringkasan", "Semua Indikator"])

# TAB 1
with tab_ringkasan:
    daftar_pilihan = [LABEL_ID[col] for col in kolom_indikator]
    pilihan_label = st.selectbox("Pilih Indikator:", daftar_pilihan)

    indikator_asli = None
    for k, v in LABEL_ID.items():
        if v == pilihan_label:
            indikator_asli = k
            break

    fig = px.line(data_filter, x="year", y=indikator_asli, markers=True)
    fig.update_layout(title_text=f"Tren {pilihan_label} - Indonesia")
    
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Sumber: World Bank (via API) • update berkala")

with tab_semua:
    kolom_kiri, kolom_kanan = st.columns(2)
    
    for i, ind in enumerate(kolom_indikator[:4]):
        # Penentuan posisi kolom
        if i % 2 == 0:
            kolom_target = kolom_kiri
        else:
            kolom_target = kolom_kanan
            
        with kolom_target:
            fig_kecil = px.line(data_filter, x="year", y=ind, markers=True)
            fig_kecil.update_layout(title_text=LABEL_ID[ind], height=300)
            st.plotly_chart(fig_kecil, use_container_width=True)
