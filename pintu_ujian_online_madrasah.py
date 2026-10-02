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

# --- CSS CUSTOM UNTUK KONTRAS DAN TAMPILAN BERSIH ---
st.markdown("""
    <style>
    html, body, [class*="css"] {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: #F8F9FA !important;
    }
    label, .stTextInput label, .stSelectbox label {
        color: #E0E0E0 !important;
        font-weight: 500;
    }
    .card-box {
        background-color: #1E2229;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #2D3748;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- KONEKSI GOOGLE SHEETS (DENGAN CACHE AGAR SUPER RINGAN) ---
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource(ttl=600)
def init_connection():
    try:
        secrets_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(secrets_dict, scopes=SCOPE)
        client = gspread.authorize(creds)
        spreadsheet = client.open("DB_Ujian_Madrasah")
        return spreadsheet
    except Exception as e:
        return None

db = init_connection()

if db is None:
    st.error("⚠️ **Gagal terhubung ke Database Google Spreadsheet.** Pastikan Secrets TOML dan nama Spreadsheet 'DB_Ujian_Madrasah' sudah benar serta dibagikan ke email Service Account.")
    st.stop()

# --- FUNGSI AMBIL DATA ---
def load_data(sheet_name):
    try:
        worksheet = db.worksheet(sheet_name)
        data = worksheet.get_all_records()
        if not data:
            return pd.DataFrame()
        return pd.DataFrame(data)
    except Exception:
        return pd.DataFrame()

# --- MANAJEMEN SESSION STATE UNTUK LOGIN & LOGOUT ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_role" not in st.session_state:
    st.session_state.user_role = ""
if "user_name" not in st.session_state:
    st.session_state.user_name = ""

# --- HALAMAN LOGIN (JIKA BELUM MASUK) ---
if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center;'>🔐 Login Panel Ujian MI Ashsholahiyah</h2>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="card-box">', unsafe_allow_html=True)
        login_sebagai = st.selectbox("Masuk Sebagai:", ["Guru / Admin", "Siswa"])
        
        with st.form("form_login"):
            username_input = st.text_input("Username / NISN")
            password_input = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Masuk Aplikasi", use_container_width=True)
            
            if submit_login:
                if login_sebagai == "Guru / Admin":
                    df_guru = load_data("guru")
                    # Cek ke database guru (jika kosong, sediakan akun default admin/admin)
                    if not df_guru.empty:
                        user_match = df_guru[(df_guru["username"].astype(str) == username_input) & (df_guru["password"].astype(str) == password_input)]
                        if not user_match.empty:
                            st.session_state.logged_in = True
                            st.session_state.user_role = "Guru"
                            st.session_state.user_name = user_match.iloc[0]["nama"]
                            st.success("Login Berhasil!")
                            st.rerun()
                        else:
                            st.error("Username atau Password Guru salah!")
                    else:
                        # Akun darurat jika sheet guru masih kosong
                        if username_input == "admin" and password_input == "1234":
                            st.session_state.logged_in = True
                            st.session_state.user_role = "Guru"
                            st.session_state.user_name = "Administrator"
                            st.success("Login Berhasil!")
                            st.rerun()
                        else:
                            st.error("Database guru kosong. Gunakan user: admin, pass: 1234")
                else:
                    # Logika Login Siswa
                    df_siswa = load_data("siswa")
                    if not df_siswa.empty:
                        siswa_match = df_siswa[(df_siswa["nisn"].astype(str) == username_input) & (df_siswa["password"].astype(str) == password_input)]
                        if not siswa_match.empty:
                            st.session_state.logged_in = True
                            st.session_state.user_role = "Siswa"
                            st.session_state.user_name = siswa_match.iloc[0]["nama"]
                            st.success("Login Siswa Berhasil!")
                            st.rerun()
                        else:
                            st.error("NISN atau Password Siswa salah!")
                    else:
                        st.error("Data siswa belum tersedia di database.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- SETELAH LOGIN BERHASIL (AREA ADMIN / GURU & SISWA) ---

# SIDEBAR: INFO USER & TOMBOL KELUAR (LOGOUT)
with st.sidebar:
    st.markdown(f"👤 **{st.session_state.user_name}**")
    st.markdown(f"Status: `{st.session_state.user_role}`")
    st.markdown("---")
    if st.button("🚪 Keluar (Logout)", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_role = ""
        st.session_state.user_name = ""
        st.cache_resource.clear()
        st.rerun()

# HEADER UTAMA
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown("### 🛠️ Panel Pengelolaan Ujian MI Ashsholahiyah")
with col_h2:
    waktu_sekarang = datetime.now().strftime("%d-%m-%Y | %H:%M")
    st.markdown(f"<p style='text-align: right; font-size: 13px; color: #A0AEC0;'>{waktu_sekarang}</p>", unsafe_allow_html=True)

st.markdown("---")

# --- MENU PENGELOLAAN MENGGUNAKAN SELECTBOX (RINGKAS & TIDAK PANJANG) ---
menu_pilihan = st.selectbox(
    "📂 Pilih Menu Navigasi:",
    [
        "👥 Manajemen Siswa & Kartu Ujian", 
        "📚 Bank Soal & Template Offline", 
        "⚙️ Pengaturan & Rilis Ujian", 
        "📊 Pemantauan Online & Pengerjaan", 
        "📈 Rekap Nilai"
    ]
)

st.markdown("<br>", unsafe_allow_html=True)

# --- HALAMAN 1: MANAJEMEN SISWA ---
if menu_pilihan == "👥 Manajemen Siswa & Kartu Ujian":
    st.markdown("#### 📖 Pengelolaan Data Siswa & Fitur Pindah Kelas")
    df_siswa = load_data("siswa")
    
    with st.container():
        st.markdown('<div class="card-box">', unsafe_allow_html=True)
        st.markdown("##### Tambah Siswa Baru (Nama Otomatis Menjadi Huruf Kapital)")
        
        with st.form("form_tambah_siswa", clear_on_submit=True):
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                input_kelas = st.text_input("Kelas (1-6)", value="5")
            with col2:
                input_no = st.text_input("No Urut", value="1")
            with col3:
                input_nisn = st.text_input("NISN / Peserta")
            with col4:
                input_nama = st.text_input("Nama Siswa")
            with col5:
                input_pass = st.text_input("Password", value="1234")
            
            submit_siswa = st.form_submit_button("💾 Simpan Data Siswa")
            
            if submit_siswa:
                if input_nisn and input_nama:
                    try:
                        sheet_siswa = db.worksheet("siswa")
                        nama_kapital = input_nama.strip().upper()
                        sheet_siswa.append_row([str(input_kelas), str(input_no), str(input_nisn), nama_kapital, str(input_pass), "Offline"])
                        st.success(f"Berhasil menyimpan siswa: {nama_kapital}")
                        st.cache_resource.clear()
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Gagal menyimpan ke Google Sheets: {ex}")
                else:
                    st.warning("Mohon isi minimal NISN dan Nama Siswa.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("##### Daftar Siswa Terdaftar di Database")
    if not df_siswa.empty:
        st.dataframe(df_siswa, use_container_width=True)
    else:
        st.info("Belum ada data siswa di dalam Google Spreadsheet.")

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
