import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Ujian MI Ashsholahiyah",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS STYLING PROFESIONAL (TEMA DARK EMERALD & KONTRAS TAJAM) ---
st.markdown("""
    <style>
    /* Global Styling */
    html, body, [class*="css"] {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: #F1F5F9 !important;
    }
    
    /* Label Form agar sangat jelas */
    label, .stTextInput label, .stSelectbox label {
        color: #E2E8F0 !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }

    /* Kartu Kontainer Elegan */
    .app-card {
        background-color: #1E293B;
        padding: 24px;
        border-radius: 12px;
        border: 1px solid #334155;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }

    /* Header Judul Utama */
    .main-title {
        font-size: 26px;
        font-weight: 700;
        color: #38BDF8;
        margin-bottom: 5px;
    }
    
    .sub-title {
        font-size: 14px;
        color: #94A3B8;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. KONEKSI GOOGLE SHEETS DENGAN CACHE ---
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource(ttl=300)
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

def load_data(sheet_name):
    try:
        worksheet = db.worksheet(sheet_name)
        data = worksheet.get_all_records()
        if not data:
            return pd.DataFrame()
        return pd.DataFrame(data)
    except Exception:
        return pd.DataFrame()

# --- 4. MANAJEMEN SESSION STATE ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_role" not in st.session_state:
    st.session_state.user_role = ""
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "user_kelas" not in st.session_state:
    st.session_state.user_kelas = ""

# =====================================================================
# HALAMAN LOGIN (TAMPILAN UTAMA KETIKA BELUM MASUK)
# =====================================================================
if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        st.markdown('<div class="app-card">', unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: #38BDF8;'>🏫 UJIAN MI ASHSHOLAHIYAH</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #94A3B8; font-size: 13px;'>Silakan masuk sesuai hak akses Anda</p><br>", unsafe_allow_html=True)
        
        login_sebagai = st.selectbox("Masuk Sebagai:", ["Guru / Admin", "Siswa"])
        
        with st.form("form_login_utama"):
            username_input = st.text_input("Username (Guru) / NISN (Siswa)")
            password_input = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Masuk Aplikasi", use_container_width=True)
            
            if submit_login:
                if login_sebagai == "Guru / Admin":
                    df_guru = load_data("guru")
                    if not df_guru.empty:
                        user_match = df_guru[(df_guru["username"].astype(str) == username_input) & (df_guru["password"].astype(str) == password_input)]
                        if not user_match.empty:
                            st.session_state.logged_in = True
                            st.session_state.user_role = "Guru"
                            st.session_state.user_name = user_match.iloc[0]["nama"]
                            st.rerun()
                        else:
                            st.error("Username atau Password Guru salah!")
                    else:
                        # Akun darurat bawaan jika database guru kosong
                        if username_input == "admin" and password_input == "1234":
                            st.session_state.logged_in = True
                            st.session_state.user_role = "Guru"
                            st.session_state.user_name = "Administrator"
                            st.rerun()
                        else:
                            st.error("Gunakan username: admin, password: 1234")
                else:
                    df_siswa = load_data("siswa")
                    if not df_siswa.empty:
                        df_siswa["nisn"] = df_siswa["nisn"].astype(str)
                        df_siswa["password"] = df_siswa["password"].astype(str)
                        siswa_match = df_siswa[(df_siswa["nisn"] == str(username_input)) & (df_siswa["password"] == str(password_input))]
                        
                        if not siswa_match.empty:
                            st.session_state.logged_in = True
                            st.session_state.user_role = "Siswa"
                            st.session_state.user_name = siswa_match.iloc[0]["nama"]
                            st.session_state.user_kelas = str(siswa_match.iloc[0]["kelas"])
                            
                            # Update status online siswa ke spreadsheet
                            try:
                                cell = db.worksheet("siswa").find(str(username_input))
                                db.worksheet("siswa").update_cell(cell.row, 6, "Online")
                            except Exception:
                                pass
                                
                            st.rerun()
                        else:
                            st.error("NISN atau Password Siswa salah!")
                    else:
                        st.error("Database siswa belum tersedia.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# =====================================================================
# SIDEBAR INFORMASI & TOMBOL KELUAR (LOGOUT)
# =====================================================================
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user_name}")
    st.markdown(f"**Hak Akses:** `{st.session_state.user_role}`")
    if st.session_state.user_role == "Siswa":
        st.markdown(f"**Kelas:** `{st.session_state.user_kelas}`")
    st.markdown("---")
    
    if st.button("🚪 Keluar (Logout)", use_container_width=True):
        if st.session_state.user_role == "Siswa":
            try:
                # Set status offline
                pass
            except Exception:
                pass
        st.session_state.logged_in = False
        st.session_state.user_role = ""
        st.session_state.user_name = ""
        st.session_state.user_kelas = ""
        st.cache_resource.clear()
        st.rerun()

# =====================================================================
# PORTAL UTAMA: JIKA YANG LOGIN ADALAH SISWA
# =====================================================================
if st.session_state.user_role == "Siswa":
    st.markdown(f"<div class='main-title'>📝 Portal Ujian Siswa - Kelas {st.session_state.user_kelas}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='sub-title'>Selamat datang, <b>{st.session_state.user_name}</b>. Silakan pilih mata pelajaran ujian yang aktif di bawah ini.</div>", unsafe_allow_html=True)
    st.markdown("---")
    
    df_pengaturan = load_data("pengaturan_ujian")
    
    if not df_pengaturan.empty:
        st.markdown("##### 📚 Daftar Jadwal Ujian Aktif")
        st.dataframe(df_pengaturan, use_container_width=True)
        st.info("💡 Hubungi guru kelas Anda jika mata pelajaran ujian belum muncul atau terkunci.")
    else:
        st.warning("Belum ada jadwal ujian yang dirilis oleh guru saat ini. Silakan menunggu.")

# =====================================================================
# PANEL UTAMA: JIKA YANG LOGIN ADALAH GURU / ADMIN
# =====================================================================
else:
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.markdown("<div class='main-title'>🛠️ Panel Pengelolaan Ujian MI Ashsholahiyah</div>", unsafe_allow_html=True)
        st.markdown("<div class='sub-title'>Dashboard Administrasi Guru & Pengelolaan Kurikulum Merdeka</div>", unsafe_allow_html=True)
    with col_h2:
        waktu_sekarang = datetime.now().strftime("%d-%m-%Y | %H:%M")
        st.markdown(f"<p style='text-align: right; font-size: 13px; color: #94A3B8;'>{waktu_sekarang}</p>", unsafe_allow_html=True)

    st.markdown("---")

    # Menu Navigasi Admin yang Ringkas & Terstruktur
    menu_pilihan = st.selectbox(
        "📂 Pilih Menu Navigasi Pengelolaan:",
        [
            "👥 Manajemen Siswa & Kartu Ujian", 
            "📚 Bank Soal & Template Offline (14 Mapel)", 
            "⚙️ Pengaturan & Rilis Ujian", 
            "📊 Pemantauan Status Online Siswa", 
            "📈 Rekapitulasi Nilai Ujian"
        ]
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # --- MENU 1: MANAJEMEN SISWA ---
    if menu_pilihan == "👥 Manajemen Siswa & Kartu Ujian":
        st.markdown("#### 📖 Pengelolaan Data Siswa")
        df_siswa = load_data("siswa")
        
        with st.container():
            st.markdown('<div class="app-card">', unsafe_allow_html=True)
            st.markdown("##### Tambah Siswa Baru (Nama Otomatis Menjadi Huruf Kapital)")
            
            with st.form("form_tambah_siswa", clear_on_submit=True):
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    input_kelas = st.text_input("Kelas", value="5")
                with col2:
                    input_no = st.text_input("No Urut", value="1")
                with col3:
                    input_nisn = st.text_input("NISN / Peserta")
                with col4:
                    input_nama = st.text_input("Nama Siswa")
                with col5:
                    input_pass = st.text_input("Password", value="1234")
                
                submit_siswa = st.form_submit_button("💾 Simpan Data Siswa", use_container_width=True)
                
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

        st.markdown("##### 📋 Daftar Seluruh Siswa Terdaftar")
        if not df_siswa.empty:
            st.dataframe(df_siswa, use_container_width=True)
        else:
            st.info("Belum ada data siswa di dalam Google Spreadsheet.")

    # --- MENU 2: BANK SOAL ---
    elif menu_pilihan == "📚 Bank Soal & Template Offline (14 Mapel)":
        st.markdown("#### 📚 Bank Soal Kurikulum Merdeka (14 Mata Pelajaran)")
        df_soal = load_data("soal")
        if not df_soal.empty:
            st.dataframe(df_soal, use_container_width=True)
        else:
            st.info("Belum ada data soal tersimpan di tab 'soal' Google Spreadsheet.")

    # --- MENU 3: PENGATURAN UJIAN ---
    elif menu_pilihan == "⚙️ Pengaturan & Rilis Ujian":
        st.markdown("#### ⚙️ Pengaturan & Rilis Jadwal Ujian")
        df_pengaturan = load_data("pengaturan_ujian")
        if not df_pengaturan.empty:
            st.dataframe(df_pengaturan, use_container_width=True)
        else:
            st.info("Belum ada data pengaturan ujian tersimpan di tab 'pengaturan_ujian'.")

    # --- MENU 4: PEMANTAUAN SISWA ---
    elif menu_pilihan == "📊 Pemantauan Status Online Siswa":
        st.markdown("#### 📊 Pemantauan Aktivitas Siswa Secara Real-Time")
        df_siswa = load_data("siswa")
        if not df_siswa.empty and "status_online" in df_siswa.columns:
            st.dataframe(df_siswa[["kelas", "nisn", "nama", "status_online"]], use_container_width=True)
        else:
            st.info("Data status siswa belum tersedia.")

    # --- MENU 5: REKAP NILAI ---
    elif menu_pilihan == "📈 Rekapitulasi Nilai Ujian":
        st.markdown("#### 📈 Rekapitulasi Nilai Hasil Ujian Siswa")
        df_nilai = load_data("nilai")
        if not df_nilai.empty:
            st.dataframe(df_nilai, use_container_width=True)
        else:
            st.info("Belum ada data nilai ujian di tab 'nilai' Google Spreadsheet.")
