import os
import pandas as pd
from data_fetchers.worldbank_fetcher import fetch_all_mvp
from forecasting.forecaster import forecast_indicator

os.makedirs("data", exist_ok=True)

df = fetch_all_mvp()
df = df[df["year"] >= 2000]

df.to_parquet("data/snapshot_indicators.parquet", index=False)

LAYAK_PREDIKSI = ["gdp_growth", "inflation", "unemployment"]
list_forecast = []

for ind in LAYAK_PREDIKSI:
    df_input = df[["year", ind]].dropna()
    
    fc = forecast_indicator(df_input)

    fc_baru = pd.DataFrame({
        "year": fc["ds"].dt.year,
        "yhat": fc["yhat"],
        "yhat_lower": fc["yhat_lower"],
        "yhat_upper": fc["yhat_upper"]
    })

    fc_baru["indicator"] = ind
    
    list_forecast.append(fc_baru)

df_forecast_gabungan = pd.concat(list_forecast, ignore_index=True)

df_forecast_gabungan.to_parquet("data/snapshot_forecasts.parquet", index=False)

print(f"File Historis : {len(df)} baris | Rentang Tahun: {df['year'].min()} - {df['year'].max()}")
print(f"File Prediksi : {len(df_forecast_gabungan)} baris | Rentang Tahun: {df_forecast_gabungan['year'].min()} - {df_forecast_gabungan['year'].max()}")