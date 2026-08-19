import json
from fastapi import FastAPI, HTTPException
from data_fetchers.worldbank_fetcher import fetch_all_mvp, INDICATORS
from api.schemas import IndicatorRecord
from data_fetchers.worldbank_fetcher import fetch_indicator
from forecasting.forecaster import forecast_indicator, FORECASTABLE
from functools import lru_cache

app = FastAPI()

# endpoint 1
@app.get("/indicators", response_model=list[IndicatorRecord])
def get_all_indicators(start_year: int = 2000, end_year: int | None = None):
    df = fetch_all_mvp()
    df = df[df["year"] >= start_year]
    if end_year is not None:
        df = df[df["year"] <= end_year]
        
    json_str = df.to_json(orient="records")
    return json.loads(json_str)

# endpoint 2
@app.get("/indicators/{indicator_id}")
def get_specific_indicator(indicator_id: str, start_year: int = 2000, end_year: int | None = None):
    if indicator_id not in INDICATORS:
        tersedia = list(INDICATORS.keys())
        raise HTTPException(
            status_code=404, 
            detail=f"Indikator '{indicator_id}' tidak ditemukan. Pilihan yang tersedia: {tersedia}"
        )
        
    df = fetch_all_mvp()
    
    df = df[df["year"] >= start_year]
    if end_year is not None:
        df = df[df["year"] <= end_year]
        
    df = df[["year", indicator_id]]
    
    json_str = df.to_json(orient="records")
    df_api = json.loads(json_str)

    return df_api

# endpoint 3

@lru_cache
def _get_forecast(indicator_id: str, horizon: int):
    code = INDICATORS[indicator_id]
    df = fetch_indicator(code, start_year=2000, end_year=2024)
    hasil = forecast_indicator(df, horizon)
    hasil["year"] = hasil["ds"].dt.year
    df = hasil[["year", "yhat", "yhat_lower", "yhat_upper"]]

    return df

@app.get("/forecast/{indicator_id}")
def get_forecast(indicator_id: str, horizon: int = 5):
    if indicator_id not in FORECASTABLE:
        raise HTTPException(404, detail=f"Hanya Indikator '{FORECASTABLE}' yang bisa dipilih")
    df = _get_forecast(indicator_id, horizon)
    json_str = df.to_json(orient="records")
    return json.loads(json_str)