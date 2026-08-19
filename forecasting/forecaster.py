import pandas as pd
from prophet import Prophet

FORECASTABLE = ["gdp_growth", "inflation", "unemployment"]

def forecast_indicator(df_indikator: pd.DataFrame, horizon: int = 5):
    df_clean = df_indikator.dropna().copy()

    kolom_nilai = [col for col in df_clean.columns if col != "year"][0]

    df_prophet = pd.DataFrame({
        "ds": pd.to_datetime(df_clean["year"].astype(str), format="%Y"),
        "y": df_clean[kolom_nilai]
    })

    model = Prophet(
        yearly_seasonality=False,
        weekly_seasonality=False,
        daily_seasonality=False
    )

    model.fit(df_prophet)
    future = model.make_future_dataframe(periods=horizon, freq="YS")

    hasil = model.predict(future)

    return hasil

if __name__ == "__main__":
    from data_fetchers.worldbank_fetcher import fetch_indicator

    data_mentah = fetch_indicator("NY.GDP.MKTP.KD.ZG", start_year=2000, end_year=2024)
    df_uji = pd.DataFrame(data_mentah)

    hasil = forecast_indicator(df_uji, horizon=5)

    print(hasil[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(8))