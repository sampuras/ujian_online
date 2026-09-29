import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(
    page_title="Portal Ujian Online Sekolah",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Styling Tombol Oval Modern & Estetik
st.markdown("""
    <style>
    .oval-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 12px 35px;
        text-align: center;
        font-size: 16px;
        font-weight: bold;
        border-radius: 50px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.2);
        display: inline-block;
        border: none;
        cursor: pointer;
    }
    </style>
""", unsafe_allow_html=True)

# Koneksi Google Sheets menggunakan gspread & secrets Streamlit
@st.cache_resource
def init_connection():
    # Menggunakan credentials dari Streamlit secrets atau Public Link via gspread
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # Jika menggunakan file JSON service account di secrets, atau mode public spreadsheet:
    # Untuk kemudahan spreadsheet publik/share:
    try:
        # Coba ambil dari st.secrets jika diset secara JSON service account
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
            client = gspread.authorize(creds)
        else:
            # Fallback jika spreadsheet diset share to anyone (read-only / write via token jika diatur)
            # Catatan: Untuk menulis (input siswa/nilai) via web publik disarankan pakai service account gratis Google Cloud.
            pass
    except Exception as e:
        st.error(f"Kesalahan autentikasi Google Sheets: {e}")
        
    # Alternatif paling praktis tanpa ribet JSON key Google Cloud (jika sheets di-share public editor):
    # Kita gunakan gspread public client atau Pandas read_csv dari link publish to web CSV.
    return None

# Cara paling stabil dan 100% gratis tanpa ribet token Google Cloud untuk membaca data:
SHEET_ID = "1yXCEf7UiKb1zKMXUPPMeB74Ge5-1p6KiJEi1GGB4DL4"

@st.cache_data(ttl=2)
py_url_siswa = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Siswa"
py_url_soal = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Soal"
py_url_nilai = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Nilai"

try:
    df_siswa = pd.read_csv(py_url_siswa)
    df_soal = pd.read_csv(py_url_soal)
    df_nilai = pd.read_csv(py_url_nilai)
except Exception as e:
    st.warning("Pastikan tab spreadsheet bernama 'Siswa', 'Soal', dan 'Nilai' sudah dibuat dan dishare publik (Anyone with the link can view).")
    df_siswa = pd.DataFrame(columns=["Kelas", "No", "NISN", "Nama"])
    df_soal = pd.DataFrame(columns=["Mapel", "KategoriUjian", "JenisSoal", "Pertanyaan", "OpsiA", "OpsiB", "OpsiC", "OpsiD", "KunciJawaban"])
    df_nilai = pd.DataFrame(columns=["NISN", "Nama", "Kelas", "Mapel", "KategoriUjian", "Nilai", "Predikat"])

def get_predikat(nilai):
    if nilai <= 40:
        return "D"
    elif nilai <= 65:
        return "C"
    elif nilai <= 85:
        return "B"
    else:
        return "A"

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_role'] = None
    st.session_state['user_data'] = None

# --- SIDEBAR TERSEMBUNYI DI POJOK KIRI ATAS ---
with st.sidebar:
    st.title("⚙️ Menu Navigasi")
    menu = st.radio("Pilih Akses", ["Portal Utama", "Login Admin", "Login Siswa"])

# --- HALAMAN UTAMA / PORTAL ---
if menu == "Portal Utama" or not st.session_state['logged_in']:
    st.markdown("<h1 style='text-align: center;'>PORTAL UJIAN ONLINE SEKOLAH TERINTEGRASI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Silakan buka menu di sidebar pojok kiri atas untuk masuk sebagai Admin atau Siswa.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Masuk Portal Siswa / Admin", use_container_width=True):
            st.info("Gunakan tombol panah kecil / menu di pojok kiri atas layar Anda.")

# --- LOGIN ADMIN ---
elif menu == "Login Admin":
    st.subheader("🔐 Login Administrator")
    admin_pass = st.text_input("Password Admin", type="password")
    if st.button("Masuk Admin"):
        if admin_pass == "adminsekolah2026":
            st.session_state['logged_in'] = True
            st.session_state['user_role'] = 'admin'
            st.success("Login Admin Berhasil!")
            st.rerun()
        else:
            st.error("Password Salah!")

    if st.session_state.get('user_role') == 'admin':
        st.divider()
        tab1, tab2, tab3 = st.tabs(["Manajemen Siswa", "Input Soal", "Rekap Nilai Siswa"])
        
        with tab1:
            st.subheader("Data Siswa Terdaftar")
            st.dataframe(df_siswa, use_container_width=True)
            st.info("Untuk menambah siswa secara online, pastikan Anda menginput langsung ke Google Sheets tab 'Siswa' agar langsung tersinkronisasi otomatis.")

        with tab2:
            st.subheader("Input Bank Soal (14 Mapel)")
            mapel_list = [
                "Akidah Akhlak", "Al-Quran Hadits", "Fiqih", "Sejarah Kebudayaan Islam (SKI)",
                "Pendidikan Pancasila", "Bahasa Indonesia", "Ilmu Pengetahuan Alam dan Sosial (IPAS)",
                "Matematika", "Pendidikan Jasmani Olahraga dan Kesehatan (PJOK)",
                "Seni Budaya dan Prakarya (SBdP)", "Bahasa Arab", "Bahasa Sunda",
                "Bahasa Inggris", "Koding dan Kecerdasan Artifisial (KKA)"
            ]
            kategori_list = ["Soal Latihan", "Soal Tengah Semester 1", "Soal Tengah Semester 2", "Soal Semester 1", "Soal Semester 2"]
            
            with st.form("form_soal"):
                m = st.selectbox("Mata Pelajaran", mapel_list)
                kat = st.selectbox("Kategori Ujian", kategori_list)
                jns = st.selectbox("Jenis Soal", ["Pilihan Ganda", "Isian", "Esai"])
                tanya = st.text_area("Pertanyaan")
                oa = st.text_input("Opsi A")
                ob = st.text_input("Opsi B")
                oc = st.text_input("Opsi C")
                od = st.text_input("Opsi D")
                kunci = st.text_input("Kunci Jawaban / Kata Kunci")
                
                if st.form_submit_button("Simpan Soal ke Database"):
                    st.success("Form soal siap disimpan. Masukkan data langsung ke Google Sheets tab 'Soal' untuk penyimpanan permanen online gratis.")

        with tab3:
            st.subheader("Rekap Nilai")
            st.dataframe(df_nilai, use_container_width=True)

# --- LOGIN SISWA ---
elif menu == "Login Siswa":
    st.subheader("🎓 Portal Masuk Siswa")
    nisn_input = st.text_input("Masukkan NISN Anda:")
    
    if st.button("Masuk Ujian"):
        cek = df_siswa[df_siswa['NISN'].astype(str).str.strip() == nisn_input.strip()]
        if not cek.empty:
            st.session_state['logged_in'] = True
            st.session_state['user_role'] = 'siswa'
            st.session_state['user_data'] = cek.iloc[0].to_dict()
            st.success(f"Selamat datang, {st.session_state['user_data']['Nama']}!")
            st.rerun()
        else:
            st.error("NISN tidak ditemukan di database siswa. Pastikan Anda sudah terdaftar.")

    if st.session_state.get('user_role') == 'siswa':
        siswa = st.session_state['user_data']
        st.info(f"Siswa Aktif: **{siswa['Nama']}** | Kelas: **{siswa['Kelas']}**")
        
        mp = st.selectbox("Pilih Mata Pelajaran", [
            "Akidah Akhlak", "Al-Quran Hadits", "Fiqih", "Sejarah Kebudayaan Islam (SKI)",
            "Pendidikan Pancasila", "Bahasa Indonesia", "Ilmu Pengetahuan Alam dan Sosial (IPAS)",
            "Matematika", "Pendidikan Jasmani Olahraga dan Kesehatan (PJOK)",
            "Seni Budaya dan Prakarya (SBdP)", "Bahasa Arab", "Bahasa Sunda",
            "Bahasa Inggris", "Koding dan Kecerdasan Artifisial (KKA)"
        ])
        kp = st.selectbox("Pilih Kategori Ujian", ["Soal Latihan", "Soal Tengah Semester 1", "Soal Tengah Semester 2", "Soal Semester 1", "Soal Semester 2"])
        
        soal_filter = df_soal[(df_soal['Mapel'].astype(str).str.strip() == mp) & (df_soal['KategoriUjian'].astype(str).str.strip() == kp)]
        
        if not soal_filter.empty:
            with st.form("kerjakan_ujian"):
                ans = {}
                score = 0
                total = len(soal_filter)
                
                for idx, row in soal_filter.iterrows():
                    st.write(f"**Soal {idx+1}:** {row['Pertanyaan']}")
                    if str(row['JenisSoal']) == 'Pilihan Ganda':
                        ans[idx] = st.radio(f"Pilihan {idx}", [row['OpsiA'], row['OpsiB'], row['OpsiC'], row['OpsiD']], key=f"s_{idx}")
                    else:
                        ans[idx] = st.text_input(f"Jawaban {idx}", key=f"s_{idx}")
                
                if st.form_submit_button("Kirim Jawaban"):
                    for idx, row in soal_filter.iterrows():
                        if str(ans[idx]).strip().lower() == str(row['KunciJawaban']).strip().lower():
                            score += (100 / total)
                    
                    final_sc = round(score, 2)
                    prd = get_predikat(final_sc)
                    st.success(f"Ujian Selesai! Nilai Anda: {final_sc} (Predikat: {prd})")
        else:
            st.warning("Belum ada soal untuk mata pelajaran dan kategori ujian ini.")
