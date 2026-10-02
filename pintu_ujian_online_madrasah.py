import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Ujian MI Ashsholahiyah",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS CUSTOM UNTUK MEMPERBAIKI KONTRAS, HURUF, DAN TAMPILAN ---
st.markdown("""
    <style>
    /* Perbaikan kontras dan kejelasan huruf secara keseluruhan */
    html, body, [class*="css"] {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: #F8F9FA !important;
    }
    
    /* Perbaikan warna teks tab / menu agar sangat jelas dibaca */
    .stTabs [data-baseweb="tab"] {
        color: #FFFFFF !important;
        font-weight: 600;
        font-size: 16px;
    }
    .stTabs [data-baseweb="tab"] [aria-selected="true"] {
        color: #4E9F3D !important;
    }

    /* Memperjelas teks label input form */
    label, .stTextInput label, .stSelectbox label {
        color: #E0E0E0 !important;
        font-weight: 500;
    }
    
    /* Kartu / Container agar lebih rapi */
    .card-box {
        background-color: #1E2229;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #2D3748;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- KONEKSI GOOGLE SHEETS (DENGAN CACHE AGAR RINGAN & TIDAK BERAT) ---
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource(ttl=600) # Data di-cache selama 10 menit agar loading super ringan
def init_connection():
    try:
        secrets_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(secrets_dict, scopes=SCOPE)
        client = gspread.authorize(creds)
        # Ganti dengan nama spreadsheet Anda di Google Drive
        spreadsheet = client.open("DB_Ujian_Madrasah")
        return spreadsheet
    except Exception as e:
        return None

db = init_connection()

if db is None:
    st.error("⚠️ **Gagal terhubung ke Database Google Spreadsheet.** Pastikan pengaturan Secrets TOML dan nama file Spreadsheet 'DB_Ujian_Madrasah' sudah benar serta sudah dibagikan ke email Service Account.")
    st.stop()

# --- FUNGSI AMBIL DATA DENGAN CACHE ---
def load_data(sheet_name):
    try:
        worksheet = db.worksheet(sheet_name)
        data = worksheet.get_all_records()
        if not data:
            return pd.DataFrame()
        return pd.DataFrame(data)
    except Exception:
        return pd.DataFrame()

# --- HEADER APLIKASI ---
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown("### 🛠️ Panel Pengelolaan Ujian MI Ashsholahiyah (GURU)")
with col_h2:
    waktu_sekarang = datetime.now().strftime("%A, %d-%m-%Y | %H:%M:%S WIB")
    st.markdown(f"<p style='text-align: right; font-size: 13px; color: #A0AEC0;'>{waktu_sekarang}</p>", unsafe_allow_html=True)

st.markdown("---")

# --- MENU UTAMA MENGGUNAKAN RADIO BUTTON (LEBIH BERSIH & TIDAK BERGESER) ---
menu_pilihan = st.radio(
    "Pilih Menu Pengelolaan:",
    [
        "👥 Manajemen Siswa & Kartu Ujian", 
        "📚 Bank Soal & Template Offline", 
        "⚙️ Pengaturan & Rilis Ujian", 
        "📊 Pemantauan Online & Pengerjaan", 
        "📈 Rekap Nilai"
    ],
    horizontal=True,
    label_visibility="collapsed"
)

st.markdown("<br>", unsafe_allow_html=True)

# --- HALAMAN 1: MANAJEMEN SISWA ---
if menu_pilihan == "👥 Manajemen Siswa & Kartu Ujian":
    st.markdown("#### 📖 Pengelolaan Data Siswa & Fitur Pindah Kelas")
    
    # Ambil data siswa
    df_siswa = load_data("siswa")
    
    with st.container():
        st.markdown('<div class="card-box">', unsafe_allow_html=True)
        st.markdown("##### Tambah Siswa Baru (Nama Otomatis Menjadi Huruf Kapital)")
        
        with st.form("form_tambah_siswa", clear_on_submit=True):
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                input_kelas = st.text_input("Kelas (1-6 / A / B)", value="5")
            with col2:
                input_no = st.text_input("No Urut", value="1")
            with col3:
                input_nisn = st.text_input("Nomor Peserta / NISN")
            with col4:
                input_nama = st.text_input("Nama Siswa")
            with col5:
                input_pass = st.text_input("Password", value="1234")
            
            submit_siswa = st.form_submit_button("💾 Simpan Data Siswa")
            
            if submit_siswa:
                if input_nisn and input_nama:
                    try:
                        sheet_siswa = db.worksheet("siswa")
                        # Format nama jadi huruf kapital
                        nama_kapital = input_nama.strip().upper()
                        sheet_siswa.append_row([str(input_kelas), str(input_no), str(input_nisn), nama_kapital, str(input_pass), "Offline"])
                        st.success(f"Berhasil menyimpan siswa: {nama_kapital}")
                        st.cache_resource.clear() # Bersihkan cache agar data langsung ter-update
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Gagal menyimpan ke Google Sheets: {ex}")
                else:
                    st.warning("Mohon isi minimal NISN dan Nama Siswa.")
        st.markdown('</div>', unsafe_allow_html=True)

    # Tampilkan Daftar Siswa yang ada di Database
    st.markdown("##### Daftar Siswa Terdaftar di Database")
    if not df_siswa.empty:
        st.dataframe(df_siswa, use_container_width=True)
    else:
        st.info("Belum ada data siswa di dalam Google Spreadsheet. Silakan tambahkan melalui form di atas.")

# --- HALAMAN 2: BANK SOAL ---
elif menu_pilihan == "📚 Bank Soal & Template Offline":
    st.markdown("#### 📚 Bank Soal & Pengelolaan Soal Ujian")
    df_soal = load_data("soal")
    if not df_soal.empty:
        st.dataframe(df_soal, use_container_width=True)
    else:
        st.info("Belum ada data soal di Google Spreadsheet (tab 'soal').")

# --- HALAMAN 3: PENGATURAN UJIAN ---
elif menu_pilihan == "⚙️ Pengaturan & Rilis Ujian":
    st.markdown("#### ⚙️ Pengaturan & Rilis Jadwal Ujian")
    df_pengaturan = load_data("pengaturan_ujian")
    if not df_pengaturan.empty:
        st.dataframe(df_pengaturan, use_container_width=True)
    else:
        st.info("Belum ada data pengaturan di Google Spreadsheet (tab 'pengaturan_ujian').")

# --- HALAMAN 4: PEMANTAUAN ---
elif menu_pilihan == "📊 Pemantauan Online & Pengerjaan":
    st.markdown("#### 📊 Pemantauan Status Siswa Secara Real-Time")
    df_siswa = load_data("siswa")
    if not df_siswa.empty and "status_online" in df_siswa.columns:
        st.dataframe(df_siswa[["kelas", "nisn", "nama", "status_online"]], use_container_width=True)
    else:
        st.info("Menunggu data siswa...")

# --- HALAMAN 5: REKAP NILAI ---
elif menu_pilihan == "📈 Rekap Nilai":
    st.markdown("#### 📈 Rekapitulasi Nilai Ujian Siswa")
    df_nilai = load_data("nilai")
    if not df_nilai.empty:
        st.dataframe(df_nilai, use_container_width=True)
    else:
        st.info("Belum ada data nilai tersimpan di Google Spreadsheet (tab 'nilai').")
