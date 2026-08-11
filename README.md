# 🗺️ Dashboard Ekonomi Indonesia Terintegrasi

> Dashboard analitik interaktif yang menyajikan data indikator makroekonomi utama Indonesia secara real-time, dilengkapi dengan fitur peramalan (*forecasting*) dan komparasi regional.

---

## 📌 Deskripsi Proyek

**Dashboard Ekonomi Indonesia** dirancang untuk menyediakan visualisasi data makroekonomi nasional yang terpusat, transparan, dan dinamis. Mengintegrasikan data resmi dari lembaga statistik nasional maupun internasional, platform ini membantu analis, peneliti, dan pengambil keputusan dalam memahami dinamika ekonomi Indonesia dengan lebih mudah.

Dashboard ini menyederhanakan kumpulan data ekonomi yang kompleks—mulai dari tren inflasi hingga proyeksi pertumbuhan PDB—menjadi wawasan visual yang siap dianalisis.

---

## ✨ Fitur Utama (Rencana Pengembangan)

### 📈 Indikator Utama (MVP)
* **Pertumbuhan PDB (GDP Growth):** Memantau laju pertumbuhan ekonomi nasional secara berkala.
* **Tingkat Inflasi:** Mengukur pergerakan harga barang/jasa dan daya beli masyarakat.
* **Tingkat Pengangguran:** Evaluasi dinamika pasar kerja dan ketersediaan lapangan kerja.
* **Tingkat Kemiskinan:** Memantau persentase penduduk berpenghasilan rendah dan efektivitas program kesejahteraan.

### 🔮 Analitik Lanjutan & Komparasi
* **Peramalan Berbasis AI (Forecasting):** Proyeksi tren indikator ekonomi menggunakan algoritma Facebook Prophet.
* **Komparasi Kawasan ASEAN:** Menganalisis posisi dan daya saing ekonomi Indonesia terhadap negara tetangga.
* **Breakdown Tingkat Provinsi:** Peta interaktif untuk melihat sebaran dan ketimpangan ekonomi antardaerah.

---

## 🗄️ Sumber Data

* **BPS (Badan Pusat Statistik):** Data nasional utama via API `stadata`.
* **World Bank Open Data:** Indikator pembanding global via `wbgapi` (kode negara: `IDN`).

---

## 🛠️ Teknologi yang Digunakan

* **Pemrosesan Data:** Python, Pandas, NumPy
* **API Layer:** FastAPI
* **Model Peramalan:** Prophet
* **Visualisasi & Antarmuka:** Streamlit, Plotly
* **DevOps & Deploy:** Docker, Hugging Face Spaces

---

## 🚀 Status Proyek

🚧 **Dalam Tahap Pengembangan** — *Minggu 1: Pembuatan Data Pipeline & Pengumpulan Data*

---

## ⚙️ Panduan Instalasi

*(Akan diperbarui setelah struktur dasar proyek stabil)*

---

## 📄 Lisensi

Proyek ini bersifat terbuka (*open-source*) di bawah lisensi [MIT License](LICENSE).