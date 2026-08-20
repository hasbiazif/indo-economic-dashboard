import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

API_URL = os.environ.get("API_URL", "http://localhost:8000")

LABEL_ID = {
    "gdp_growth":   "Pertumbuhan PDB (%)",
    "inflation":    "Inflasi IHK (%)",
    "unemployment": "Pengangguran (%)",
    "poverty":      "Kemiskinan (%)",
}

LAYAK_PREDIKSI = ["gdp_growth", "inflation", "unemployment"]

st.set_page_config(page_title="Dashboard World Bank", layout="wide")
st.title("Visualisasi Dashboard World Bank")

@st.cache_data(ttl=3600, show_spinner="Mengambil data indikator...")
def fetch_data():
    try:
        response = requests.get(f"{API_URL}/indicators", params={"start_year": 2000})
        response.raise_for_status()
        return pd.DataFrame(response.json())

    except requests.exceptions.RequestException:
        try:
            df_fallback = pd.read_parquet("data/snapshot_indicators.parquet")
            return df_fallback

        except Exception as ex:
            return pd.DataFrame()

@st.cache_data(show_spinner="Mengambil data prediksi...")
def fetch_forecast(indikator_key: str):
    try:
        response = requests.get(f"{API_URL}/forecast/{indikator_key}")
        response.raise_for_status()
        return pd.DataFrame(response.json())
    
    except requests.exceptions.RequestException:
        try:
            df_fallback = pd.read_parquet("data/snapshot_forecasts.parquet")
            df_terfilter = df_fallback[df_fallback["indicator"] == indikator_key]
            return df_terfilter

        except Exception as e:
            return pd.DataFrame()

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
tab_ringkasan, tab_semua, tab_prediksi = st.tabs(["Ringkasan", "Semua Indikator", "Prediksi"])

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
    
    st.plotly_chart(fig, width="stretch")
    st.caption("Sumber: World Bank (via API) • update berkala")

# TAB 2
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
            st.plotly_chart(fig_kecil, width="stretch")


# TAB 3
with tab_prediksi:
    opsi_label = [LABEL_ID[k] for k in LAYAK_PREDIKSI]
    pilihan_label2 = st.selectbox("Pilih Indikator :", opsi_label)

    key_terpilih = [k for k, v in LABEL_ID.items() if v == pilihan_label2][0]

    try:
        fc = fetch_forecast(key_terpilih)

        fc_depan = fc[fc["year"] >= 2025]

        df_historis = data_filter[["year", key_terpilih]].dropna()

        fig = go.Figure()

        # a. HISTORIS
        fig.add_trace(go.Scatter(
            x=df_historis["year"],
            y=df_historis[key_terpilih],
            mode="lines+markers",
            name="Data Historis",
            line=dict(color="blue", width=2)
        ))

        # b. BATAS BAWAH
        fig.add_trace(go.Scatter(
            x=fc_depan["year"],
            y=fc_depan["yhat_lower"],
            mode="lines",
            name="Batas Bawah",
            line=dict(width=0), # Garis dibuat tidak terlihat
            showlegend=False
        ))

        # c. BATAS ATAS
        fig.add_trace(go.Scatter(
            x=fc_depan["year"],
            y=fc_depan["yhat_upper"],
            mode="lines",
            name="Rentang Kepercayaan",
            line=dict(width=0),
            fill="tonexty", 
            fillcolor="rgba(255, 165, 0, 0.2)" # Nilai 0.2 adalah tingkat transparansi
        ))

        # d. PREDIKSI
        fig.add_trace(go.Scatter(
            x=fc_depan["year"],
            y=fc_depan["yhat"],
            mode="lines+markers",
            name="Prediksi (Prophet)",
            line=dict(color="orange", width=2, dash="dash")
        ))

        fig.update_layout(
            title=f"Prediksi {pilihan_label2} - Indonesia",
            xaxis_title="Tahun",
            yaxis_title="Nilai",
            hovermode="x unified" # Memunculkan satu kotak tooltip untuk semua garis di tahun yang sama
        )

        st.plotly_chart(fig, width="stretch")

    except Exception as e:
        st.error(f"Terjadi kesalahan saat memuat prediksi: {e}")
        
