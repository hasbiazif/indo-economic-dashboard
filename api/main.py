import json
from fastapi import FastAPI
from data_fetchers.worldbank_fetcher import fetch_all_mvp

app = FastAPI()

@app.get("/indicators")
def get_worldbank_data(start_year: int = 2000, end_year: int | None = None):
    df = fetch_all_mvp()
    df = df[df["year"] >= start_year]
    if end_year is not None:
        df = df[df["year"] <= end_year]
    json_str = df.to_json(orient="records")
    df_api = json.loads(json_str)

    return df_api