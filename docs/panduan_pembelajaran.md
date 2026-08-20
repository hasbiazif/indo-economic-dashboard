# 📚 Panduan Pembelajaran: Membangun Dashboard Ekonomi End-to-End

> Dokumentasi langkah-demi-langkah project **Indonesian Economic Dashboard** — ditulis sebagai panduan belajar, bukan sekadar dokumentasi kode. Membacanya ulang = mengulang seluruh perjalanan: dari data mentah sampai live demo.
>
> Cara pakai: tiap bagian berisi **Konsep → Langkah → Lesson yang saya alami sendiri**. Kalau mau membangun hal serupa, ikuti urutannya.

---

## Daftar Isi

1. [Gambaran Arsitektur](#1-gambaran-arsitektur)
2. [Setup Project & Environment](#2-setup-project--environment)
3. [Layer Data: Fetcher World Bank](#3-layer-data-fetcher-world-bank)
4. [Layer API: FastAPI](#4-layer-api-fastapi)
5. [Layer ML: Forecasting Prophet](#5-layer-ml-forecasting-prophet)
6. [Layer Presentasi: Dashboard Streamlit](#6-layer-presentasi-dashboard-streamlit)
7. [Docker: Containerization](#7-docker-containerization)
8. [Snapshot Parquet & Fallback Offline](#8-snapshot-parquet--fallback-offline)
9. [Deploy ke Streamlit Cloud](#9-deploy-ke-streamlit-cloud)
10. [Kumpulan Lesson Learned](#10-kumpulan-lesson-learned)
11. [Cheatsheet Perintah](#11-cheatsheet-perintah)

---

## 1. Gambaran Arsitektur

Project ini punya 4 layer yang **terpisah tanggung jawabnya** — prinsip yang sama dengan aplikasi profesional:

```
World Bank API (wbgapi)
        │
        ▼
data_fetchers/  ──(export)──►  data/*.parquet (snapshot offline)
        │
        ▼
forecasting/ (Prophet)
        │
        ▼
api/ (FastAPI + uvicorn)  ◄── HTTP JSON ──  dashboard/ (Streamlit + Plotly)
```

**Kenapa dipisah-pisah?**
- `dashboard/` TIDAK import `forecasting` atau `data_fetchers` — dia murni konsumen HTTP. Akibatnya: dashboard bisa di-deploy ringan tanpa Prophet.
- Tiap layer bisa diganti tanpa merusak lainnya (misal ganti Streamlit → Gradio, API tetap).
- Ini contoh nyata prinsip *separation of concerns*.

---

## 2. Setup Project & Environment

### Konsep
- **Environment manager**: `uv` (cepat, modern) dengan mode `uv pip` + `requirements.txt`
- **Python 3.13**: versi terbaru — keputusan berisiko (beberapa library belum support), tapi terbukti jalan
- **Git dari hari pertama** + repo GitHub publik: portofolio butuh riwayat commit yang jujur

### Langkah
```
1. git init + buat repo GitHub publik (via gh / web)
2. python -m venv .venv        (atau uv venv)
3. aktifkan: .venv\Scripts\activate   (Windows)
4. uv pip install <package>    per layer
5. catat dependency: uv pip freeze > requirements.txt  (atau tulis manual)
6. .gitignore SEBELUM commit pertama:
   .venv/, __pycache__/, .env, cache/, *.pyc
```

### Lesson
- ⚠️ **`.env` (API key) wajib di-`.gitignore` sebelum commit pertama.** Secret yang pernah ter-commit tetap ada di history git walau file-nya dihapus.
- **Commit = asuransi.** Saya pernah menimpa `Dockerfile` dengan versi lain karena belum commit — tidak ada jalan mundur. Commit tiap checkpoint hijau, sekecil apa pun.

---

## 3. Layer Data: Fetcher World Bank

### Konsep
- **wbgapi**: client resmi World Bank API. Data indikator = kode seri (mis. `NY.GDP.MKTP.KD.ZG` = GDP growth).
- **`functools.lru_cache`**: fetch jaringan itu mahal — cache hasil di memori supaya panggilan berulang tidak download ulang.
- **Dataframe wide**: baris = tahun, kolom = satu indikator per kolom. Format ini yang dipakai semua layer di hilir.

### Langkah
```
1. Definisikan dict INDIKATOR = {key: kode_wb, ...}
2. Fungsi fetch_indicator(key) → DataFrame(year, nilai)
   - guard: kalau hasil kosong → raise/error jelas
   - optional param tahun via **params
3. Fungsi fetch_all_mvp() → merge 4 indikator jadi 1 wide DF
4. Dekorasi @lru_cache di fungsi fetch
5. Test: python -m data_fetchers.worldbank_fetcher
```

### Lesson
- ⚠️ **Jalankan file dalam package pakai `python -m data_fetchers.worldbank_fetcher` dari root** — bukan `python data_fetchers/worldbank_fetcher.py`. Script mode tidak melihat sibling package (sys.path-nya folder script, bukan cwd). Ini pernah bikin bingung berjam-jam.

---

## 4. Layer API: FastAPI

### Konsep
- **FastAPI + uvicorn**: framework API modern Python, otomatis punya docs interaktif di `/docs` (Swagger).
- **Pydantic response_model**: kontrak bentuk respons — validasi otomatis, dokumentasi gratis.
- **NaN → null**: JSON tidak mengenal NaN; pandas `to_json` mengubahnya jadi `null` — round-trip `df.to_json()` + `json.loads()` adalah cara aman menserialisasi.

### Langkah
```
1. api/schemas.py — Pydantic model IndicatorRecord (year: int, indikator: float | None)
2. api/main.py — app = FastAPI()
   GET /indicators         → list[IndicatorRecord], query param start_year/end_year
   GET /indicators/{id}    → 404 kalau id tak dikenal (HTTPException)
   GET /forecast/{id}      → hasil Prophet, helper @lru_cache, 404 kalau tak layak prediksi
3. Jalankan: uvicorn api.main:app --reload  (dari root!)
4. Test di browser: http://localhost:8000/docs
```

### Lesson
- ⚠️ **Proses uvicorn kadang jadi "zombie"** menahan port 8000 (Ctrl+C tidak matikan bersih). Deteksi: `netstat -ano | findstr :8000` → `taskkill //PID <pid> //F`.
- Endpoint yang lambat (Prophet ±5 detik) → bungkus dengan cache agar tidak hitung ulang tiap request.

---

## 5. Layer ML: Forecasting Prophet

### Konsep
- **Prophet** (Meta): model time-series aditif — trend + seasonality + holiday. Untuk data tahunan ekonomi: **seasonality dimatikan semua** (tidak ada pola mingguan/bulanan di data tahunan).
- **Format input wajib**: DataFrame dengan kolom `ds` (datetime) & `y` (nilai).
- **Output `predict()`**: `yhat` (prediksi) + `yhat_lower`/`yhat_upper` (rentang ketidakpastian) — plus banyak kolom diagnostic lain.
- **freq="YS"**: year-start — memberi tahu Prophet periode data kita tahunan.

### Langkah
```
1. Siapkan df: ds = to_datetime(year, format="%Y"), y = nilai
2. model = Prophet(yearly_seasonality=False, weekly_seasonality=False, daily_seasonality=False)
3. model.fit(df)
4. future = model.make_future_dataframe(periods=5, freq="YS")
5. hasil = model.predict(future)
6. Filter output ke kolom yang dibutuhkan: year (dari ds.dt.year), yhat, yhat_lower, yhat_upper
```

### Lesson
- 🔥 **Insight modeling terpenting project ini**: melatih dengan full-history (1960→) membuat pita forecast melebar drastis — hiperinflasi & krisis 1998 "masuk" ke model dan menaikkan variance. Solusi: **batasi era data ≥2000**. Pelajaran umum: data historis yang jauh berbeda rezim bisa merusak model — selalu pikirkan konteks.
- ⚠️ Prophet + Python 3.13 sempat diragukan kompatibilitasnya — ternyata prophet 1.4.0 jalan normal. Verifikasi > asumsi.

---

## 6. Layer Presentasi: Dashboard Streamlit

### Konsep
- **Streamlit**: app Python murni — script dijalankan ulang dari atas setiap interaksi. Makanya `@st.cache_data` penting (fetch tidak diulang tiap klik).
- **`st.metric`**: KPI card dengan delta otomatis.
- **Guard**: data 1 tahun → `iloc[-2]` error → selalu cek `len >= 2` sebelum hitung delta.
- **Plotly dua API**: `px.line` untuk cepat, `go.Figure` untuk kontrol penuh (uncertainty band).

### Langkah
```
1. Struktur halaman: set_page_config → title → sidebar/slider → KPI columns → tabs
2. fetch_data + fetch_forecast via requests ke API (konsumen murni HTTP)
3. Slider rentang tahun → filter df
4. 3 tab: Ringkasan (selectbox+chart) / Semua Indikator (grid 2×2 st.columns) / Prediksi
5. Chart prediksi 4 trace go.Figure:
   historis (garis biru) → lower (invisible line width=0) → upper (fill="tonexty", rgba oranye)
   → prediksi (dash oranye)
6. try/except di sekitar forecast + st.error agar tab lain tetap hidup kalau gagal
```

### Lesson
- ⚠️ **Konfigurasi via env var**: `API_URL = os.environ.get("API_URL", "http://localhost:8000")` — pola 12-factor. Tanpa ini, tidak ada cara mengarahkan dashboard ke container API tanpa edit kode.
- ⚠️ **Jangan tampilkan `st.error`/`st.warning` di dalam fungsi `@st.cache_data`** — UI call ikut ter-cache dan pesannya bisa "membeku" tidak sesuai kondisi. Fungsi cache: return data saja; pesan di luar.
- ⚠️ `use_container_width` deprecated (2025) → ganti `width="stretch"`.

---

## 7. Docker: Containerization

Bagian terbesar pembelajaran project ini. Dibaca bertahap.

### 7a. Konsep Dasar

| Istilah | Arti |
|---|---|
| **Image** | "Foto" beku dari sistem + app — template hanya-baca |
| **Container** | Instance yang berjalan dari image |
| **Dockerfile** | Resep memasak image (instruksi berlapis) |
| **Layer** | Hasil tiap instruksi; di-cache dan dipakai bersama antar image |
| **Build context** | Folder yang "terlihat" Docker saat build — menentukan apa yang boleh di-COPY |

### 7b. Layer Caching — urutan Dockerfile menentukan kecepatan

```dockerfile
FROM python:3.13-slim              # base: jarang berubah
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt .            # ← requirements DULU
RUN pip install --no-cache-dir -r requirements.txt   # MAHAL — hanya rerun kalau requirements berubah
COPY api/ ./api/                   # kode — sering berubah, taruh BELAKANG
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Kalau `COPY . .` dilakukan sebelum pip install → tiap ubah 1 baris kode = install ulang semua deps.

### 7c. Konsep penting lain per instruksi

- `EXPOSE` = **dokumentasi saja** — tidak membuka port. Pemetaan port asli: `docker run -p HOST:CONTAINER`.
- `CMD` wajib **exec-form** `["program", "arg"]` (bukan shell-form) agar sinyal SIGTERM diteruskan benar.
- **`--host 0.0.0.0` wajib di dalam container** — kalau listen 127.0.0.1, tidak ada yang bisa masuk dari luar container.
- `--no-cache-dir` di pip = hemat ratusan MB di image.
- **`.dockerignore`** seperti `.gitignore` — `.venv/`, `.git/`, dan terutama `.env` (secret!) tidak boleh masuk image.

### 7d. Networking — pelajaran paling penting Docker

> **`localhost` di dalam container = container itu sendiri. BUKAN laptop host.**

| Skenario | Cara panggil API |
|---|---|
| Browser laptop → container | `http://localhost:8000` (lewat mapping `-p`) |
| Container A → laptop host | `http://host.docker.internal:8000` (Docker Desktop) |
| Container → container (compose, satu network) | `http://api:8000` — **nama service = hostname** |
| Proses → proses (SATU container) | `http://localhost:8000` — satu network namespace, localhost berfungsi normal |

### 7e. Tiga artefak Docker project ini

**1. Dockerfile (root) — image API**
```
COPY api/ data_fetchers/ forecasting/ → uvicorn port 8000
(api meng-import forecasting utk endpoint /forecast — cek import sebelum menentukan COPY!)
```

**2. dashboard/Dockerfile — image dashboard**
```
COPY dashboard/ saja (dashboard tidak import layer lain) → streamlit port 8501
Build: docker build -t econ-dash -f dashboard/Dockerfile .   ← -f + context root
```

**3. deploy/Dockerfile + start.sh — single container (API + dashboard 1 image)**
```bash
#!/bin/bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 &     # & = background
exec streamlit run dashboard/app.py --server.address=0.0.0.0 --server.port 7860
```
- `&` = jalankan di background (tidak menahan baris berikutnya)
- `exec` di baris terakhir = ganti proses shell dengan streamlit → streamlit jadi PID 1 → sinyal (SIGTERM/stop) diterima langsung, container mati bersih
- `#!/bin/bash` (shebang) = memberi tahu kernel interpreter script ini
- Non-root user wajib di banyak platform (HF Spaces, OpenShift):
  `RUN useradd -m -u 1000 appuser` → `chown -R appuser /app` → `USER appuser`

**4. docker-compose.yml — orkestrasi**
```yaml
services:
  api:
    image: econ-api            # nama TAG hasil build (harus UNIK per service!)
    build:
      context: .
      dockerfile: Dockerfile
    ports: ["8000:8000"]
  dashboard:
    image: econ-dash
    build:
      context: .
      dockerfile: dashboard/Dockerfile
    ports: ["8501:8501"]
    environment:
      API_URL: http://api:8000   # nama service sebagai hostname
    depends_on: [api]            # urutan start saja, BUKAN menunggu siap
```

### Lesson Docker (semua pernah saya alami)
- ⚠️ **Build context menentukan apa yang bisa di-COPY**: build dari `dashboard/` tidak bisa COPY `requirements.txt` di root. Solusi: selalu build dari root + `-f`.
- ⚠️ **Image = template beku; container = instance.** `docker start` TIDAK membaca image baru — harus `docker rm` + `run` ulang (atau `compose up --build` yang me-recreate otomatis).
- ⚠️ **CMD harus persis = tujuan COPY**: `COPY x /start.sh` ↔ `CMD ["/start.sh"]`. Campur `/start.sh` ↔ `./start.sh` = "no such file or directory" yang membingungkan.
- ⚠️ **CRLF (Windows) membunuh .sh**: Linux membaca `\r` sebagai karakter → "no such file or directory" padahal file ada. Cek dengan `od -c`; cegah dengan editor set LF atau `.gitattributes`: `*.sh text eol=lf`.
- ⚠️ **`image:` di compose harus unik per service** — saya pernah salah tulis `econ-api` di dua service, tag saling menimpa.
- ⚠️ **Race condition startup**: `depends_on` hanya urutan, bukan "menunggu siap". Dashboard bisa mengetuk API sebelum uvicorn siap → error sekali di load pertama, normal setelahnya.
- 💡 **Layer sharing**: 4 image dengan resep mirip tidak makan 4× disk — layer yang sama disimpan sekali. `docker system df` menunjukkan angka sebenarnya.
- 💡 **Vhdx WSL2 tidak menyusut otomatis** walau image dihapus — bersihkan berkala: `docker system prune` (jangan `-a` kalau tidak mau build dari nol).

---

## 8. Snapshot Parquet & Fallback Offline

### Konsep
- **Kenapa**: dashboard di cloud tidak punya API hidup → butuh data beku yang di-bundle ke repo.
- **Parquet**: format kolom binary — kecil, cepat, tipe data terjaga (vs CSV: teks semua).
- **Skema konsisten**: parquet harus punya kolom PERSIS seperti JSON API (`year, yhat, yhat_lower, yhat_upper` + kolom `indicator`) supaya fallback tidak butuh ubah kode dashboard.

### Langkah
```
1. data_fetchers/export_snapshot.py:
   - os.makedirs("data", exist_ok=True)
   - historis: fetch_all_mvp() → filter ≥2000 → data/snapshot_indicators.parquet
   - forecast: loop 3 indikator → forecast_indicator() → PILIH HANYA kolom
     year (dari ds.dt.year), yhat, yhat_lower, yhat_upper → + kolom indicator
     → pd.concat → data/snapshot_forecasts.parquet
   - print sanity check (jumlah baris + rentang tahun)
2. .gitignore: hapus *.parquet / pastikan data/ tidak ter-ignore
   → verifikasi: git check-ignore -v data/xxx.parquet  (output KOSONG = benar)
3. dashboard/app.py: try requests → except RequestException → pd.read_parquet
   (forecast: read + filter indicator == key)
```

### Lesson
- ⚠️ **Bug skema produsen↔konsumen**: export menyimpan kolom mentah Prophet (`ds`, dll) padahal dashboard membaca `fc["year"]` → KeyError di tempat lain, jauh dari penyebabnya. Selalu samakan skema lintas layer **di titik produksi**.
- ⚠️ **`.dt` hanya untuk kolom datetime** — `AttributeError: Can only use .dt accessor with datetimelike values` berarti kolom sudah integer. Setelah konversi `ds→year`, hapus `.dt.year` di kode hilir.
- ⚠️ **`except:` telanjang itu jebakan** — menangkap semua termasuk bug ketik, dan `f"{e}"` tanpa `as e` = NameError di dalam handler. Pakai `except requests.RequestException as e:`.
- 💡 **Bonus arsitektur**: API key (BPS nantinya) tidak pernah keluar dari laptop — yang di-push ke cloud hanya data jadi. Keamanan by design.

---

## 9. Deploy ke Streamlit Cloud

### Konsep
- **Streamlit Community Cloud**: gratis, deploy langsung dari repo GitHub publik, **auto-redeploy setiap push ke main**.
- Keterbatasan: 1 GB RAM, app tidur ±12 jam idle (bangun saat dikunjungi, tunggu ~30–60 dtk).

### Langkah
```
1. Pastikan repo publik + parquet ter-commit + requirements.txt benar
2. share.streamlit.io → sign in with GitHub
3. New app: pilih repo → branch main → main file: dashboard/app.py
4. Deploy → tunggu 2–5 menit → URL *.streamlit.app
5. Setiap git push ke main = demo ter-update otomatis
```

### Konteks keputusan (penting untuk dipahami, bukan sekadar fakta)
- Rencana awal: HuggingFace Spaces (Docker SDK). **Juli 2026 HF mengubah kebijakan**: Docker SDK jadi berbayar (PRO $9/bln), Streamlit SDK deprecated, akun gratis baru hanya bisa Static/ZeroGPU → pivot ke Streamlit Cloud.
- Pelajaran: **kebijakan platform gratis bisa berubah kapan saja** — desain yang portabel (container image siap, data snapshot terpisah dari platform) membuat pivot tinggal ganti target deploy.
- Image Docker tetap di repo & teruji lokal → skill-nya tetap ada, story engineering-nya tetap bisa diceritakan.

---

## 10. Kumpulan Lesson Learned

### Python & Package
- `python -m package.modul` dari root, bukan `python folder/file.py` (sys.path)
- lru_cache untuk fungsi jaringan; st.cache_data untuk fungsi di Streamlit (beda konteks!)
- venv per project; requirements.txt = manifest yang bisa direproduksi

### Data & Modeling
- NaN tidak ada di JSON → round-trip to_json + json.loads
- Pikirkan rezim data historis sebelum melatih (1998!)
- Skema lintas layer harus dikunci di titik produksi

### Streamlit
- Cache menyimpan UI call juga — keluarkan pesan error dari fungsi cache
- Guard edge case (data 1 tahun) sebelum iloc[-2]
- Ikuti deprecation warning sebelum jadi error

### Docker
- localhost dalam container ≠ localhost host (lihat tabel 7d)
- Urutan Dockerfile = strategi caching
- CMD exec-form + path persis = tujuan COPY
- CRLF membunuh .sh dari Windows
- image: di compose unik per service
- rm + run ulang setelah build baru (container membeku konfigurasi lama)

### Git & Workflow
- Commit tiap checkpoint — file tak ter-commit tidak punya jaring pengaman
- .gitignore negation (`!`) punya jebakan urutan — selalu verifikasi dengan git check-ignore -v
- Jangan commit secret (.env) — dan jangan commit draf personal (post LinkedIn, catatan) ke repo publik

---

## 11. Cheatsheet Perintah

### Python
```bash
python -m venv .venv && .venv\Scripts\activate     # setup
uv pip install -r requirements.txt                  # install
python -m data_fetchers.export_snapshot             # jalanin modul dari root
uvicorn api.main:app --reload                       # API lokal
streamlit run dashboard/app.py                      # dashboard lokal
```

### Docker
```bash
docker build -t econ-api .                          # build image (Dockerfile root)
docker build -t econ-dash -f dashboard/Dockerfile . # build dengan Dockerfile lain, context root
docker run -d -p 8000:8000 --name api econ-api      # jalan + map port (HOST:CONTAINER)
docker run -d -p 8501:8501 -e API_URL=http://host.docker.internal:8000 econ-dash
docker ps -a                                        # daftar container
docker logs <nama>                                  # baca log (debugging pertama!)
docker exec -it <nama> ls /app                      # masuk container lihat isi
docker rm -f <nama>                                 # hapus container
docker rmi <image>                                  # hapus image
docker images / docker system df                    # lihat image & pemakaian disk
docker system prune                                 # bersihkan (tanpa -a!)
```

### Docker Compose
```bash
docker compose up -d --build     # nyalakan stack (build jika perlu)
docker compose ps                # status
docker compose logs -f dashboard # log satu service
docker compose down              # matikan semua
```

### Git
```bash
git status --short               # lihat yang berubah
git check-ignore -v <file>       # selidiki kenapa file di-ignore
git add -p                       # stage per potongan (review sebelum commit)
git commit -m "feat: ..."        # conventional commits: feat/fix/docs/refactor
git log --oneline                # riwayat ringkas
```

### Windows khusus
```bash
netstat -ano | findstr :8000     # siapa pegang port 8000
taskkill //PID <pid> //F         # paksa matikan proses (uvicorn zombie)
od -c file.sh                    # deteksi CRLF vs LF
```

---

## Penutup

Project ini membuktikan siklus lengkap: **data → API → ML → dashboard → container → live demo** — masing-masing layer dengan keputusan desain yang bisa dipertanggungjawabkan dan didokumentasikan.

Iterasi berikutnya yang sudah teridentifikasi:
- [ ] Integrasi BPS API (neraca perdagangan) — key tetap lokal, cloud hanya terima parquet
- [ ] Komparasi ASEAN (multi-negara WB)
- [ ] Tests (pytest) untuk fetcher & API
- [ ] Optimasi requirements.txt ramping untuk build cloud lebih cepat

> Dokumen ini ditulis sebagai panduan belajar pribadi dengan bantuan AI (Claude) sebagai mentor — seluruh kode dan keputusan diimplementasikan sendiri sebagai bagian dari proses belajar.
