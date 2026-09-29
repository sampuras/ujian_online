import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Portal Ujian Online Sekolah",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Styling Tombol Oval Modern & Estetik
st.markdown("""
    <style>
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 10px 24px;
        font-size: 16px;
        font-weight: bold;
        border-radius: 30px;
        border: none;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.2);
        transition: 0.3s;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0px 6px 20px rgba(0,0,0,0.3);
    }
    </style>
""", unsafe_allow_html=True)

# ID Google Sheets Anda
SHEET_ID = "1yXCEf7UiKb1zKMXUPPMeB74Ge5-1p6KiJEi1GGB4DL4"

# Membaca Data dari Google Sheets via CSV Export
@st.cache_data(ttl=2)
def load_data():
    url_siswa = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Siswa"
    url_soal = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Soal"
    url_nilai = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Nilai"
    
    try:
        df_s = pd.read_csv(url_siswa)
    except:
        df_s = pd.DataFrame(columns=["Kelas", "No", "NISN", "Nama"])
        
    try:
        df_q = pd.read_csv(url_soal)
    except:
        df_q = pd.DataFrame(columns=["Mapel", "KategoriUjian", "JenisSoal", "Pertanyaan", "OpsiA", "OpsiB", "OpsiC", "OpsiD", "KunciJawaban"])
        
    try:
        df_n = pd.read_csv(url_nilai)
    except:
        df_n = pd.DataFrame(columns=["NISN", "Nama", "Kelas", "Mapel", "KategoriUjian", "Nilai", "Predikat"])
        
    return df_s, df_q, df_n

df_siswa, df_soal, df_nilai = load_data()

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
    
    if st.session_state['logged_in']:
        st.divider()
        if st.button("Keluar (Logout)"):
            st.session_state['logged_in'] = False
            st.session_state['user_role'] = None
            st.session_state['user_data'] = None
            st.rerun()

# --- HALAMAN UTAMA / PORTAL ---
if menu == "Portal Utama" or not st.session_state['logged_in']:
    st.markdown("<h1 style='text-align: center;'>PORTAL UJIAN ONLINE SEKOLAH TERINTEGRASI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Silakan klik ikon panah kecil di pojok kiri atas untuk membuka menu login Admin atau Siswa.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if df_siswa.empty:
            st.warning("⚠️ Perhatian: Database siswa di Google Sheets belum terbaca atau masih kosong. Pastikan link Google Sheets sudah di-share publik.")

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
            st.info("💡 Tambah data siswa langsung di Google Sheets pada tab 'Siswa' lalu refresh halaman.")

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
                
                if st.form_submit_button("Simpan Soal"):
                    st.success("Format soal tercatat. Silakan masukkan data soal ke Google Sheets tab 'Soal'.")

        with tab3:
            st.subheader("Rekap Nilai Siswa")
            st.dataframe(df_nilai, use_container_width=True)

# --- LOGIN SISWA ---
elif menu == "Login Siswa":
    st.subheader("🎓 Portal Masuk Siswa")
    nisn_input = st.text_input("Masukkan NISN Anda:")
    
    if st.button("Masuk Ujian"):
        if df_siswa.empty:
            st.error("Database siswa belum tersambung ke Google Sheets.")
        else:
            # Pencocokan NISN
            cek = df_siswa[df_siswa['NISN'].astype(str).str.strip() == str(nisn_input).strip()]
            if not cek.empty:
                st.session_state['logged_in'] = True
                st.session_state['user_role'] = 'siswa'
                st.session_state['user_data'] = cek.iloc[0].to_dict()
                st.success(f"Selamat datang, {st.session_state['user_data']['Nama']}!")
                st.rerun()
            else:
                st.error("NISN tidak ditemukan di database siswa. Pastikan Anda sudah terdaftar di Google Sheets.")

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
            st.warning("Belum ada soal untuk mata pelajaran dan kategori ujian ini di Google Sheets.")
