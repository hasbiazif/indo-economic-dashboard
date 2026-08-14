import pandas as pd
import wbgapi as wb
from functools import lru_cache

INDICATORS = {
    "gdp_growth": "NY.GDP.MKTP.KD.ZG",
    "inflation": "FP.CPI.TOTL.ZG",
    "unemployment": "SL.UEM.TOTL.ZS",
    "poverty": "SI.POV.NAHC"
}

def fetch_indicator(indicator_code, country="IDN", start_year=None, end_year=None):

    params = {
        "economy": country,
        "labels": False
    }

    if (start_year is None and end_year is not None) or (start_year is not None and end_year is None):
        raise ValueError("Error: start_year dan end_year harus diisi keduanya, atau kosongkan keduanya.")

    if start_year is not None and end_year is not None:
        params["time"] = range(start_year, end_year + 1)

    # Mengambil data dari World Bank API
    df = wb.data.DataFrame(indicator_code, **params)

    if df.empty:
        raise ValueError(f"Data tidak ditemukan untuk indikator '{indicator_code}'.")
    
    # Merapikan struktur DataFrame (mengubah index time dari 'YR2000' menjadi angka/integer tahun)
    df = df.T.reset_index()
    df.columns = ["year", "value"]
    df["year"] = df["year"].str.replace("YR", "").astype(int)
    
    return df

@lru_cache
def fetch_all_mvp():
    combined_df = None
    
    for name, code in INDICATORS.items():
        # Ambil data per indikator
        df_single = fetch_indicator(code)
        df_single = df_single.rename(columns={"value": name})
        
        # Gabungkan berdasarkan kolom 'year'
        if combined_df is None:
            combined_df = df_single
        else:
            combined_df = pd.merge(combined_df, df_single, on="year", how="outer")
            
    return combined_df.sort_values("year").reset_index(drop=True)

if __name__ == "__main__":
    df = fetch_all_mvp()
    print("\nHead DataFrame:")
    print(df.head())
    print("\nTail DataFrame:")
    print(df.tail())