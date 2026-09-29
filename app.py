import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(
    page_title="Portal Ujian Online Sekolah",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Styling Tombol Oval Modern
st.markdown("""
    <style>
    .oval-btn {
        background: linear-gradient(135deg, #4e54c8, #8f94fb);
        border: none;
        color: white;
        padding: 12px 30px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        font-weight: bold;
        border-radius: 30px;
        cursor: pointer;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.2);
    }
    </style>
""", unsafe_allow_html=True)

# Koneksi Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    df_siswa = conn.read(worksheet="Siswa", ttl=2)
    df_soal = conn.read(worksheet="Soal", ttl=2)
    df_nilai = conn.read(worksheet="Nilai", ttl=2)
except Exception as e:
    st.error(f"Gagal memuat database Google Sheets. Pastikan nama worksheet benar. Error: {e}")
    st.stop()

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

# Sidebar Tersembunyi di Pojok Kiri Atas
with st.sidebar:
    st.title("⚙️ Menu Navigasi")
    menu = st.radio("Pilih Akses", ["Portal Utama", "Login Admin", "Login Siswa"])

if menu == "Portal Utama" or not st.session_state['logged_in']:
    st.markdown("<h1 style='text-align: center;'>SELAMAT DATANG DI PORTAL UJIAN ONLINE SEKOLAH</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Gunakan menu di sidebar pojok kiri atas untuk masuk.</p>", unsafe_allow_html=True)

elif menu == "Login Admin":
    st.subheader("🔐 Login Administrator")
    admin_pass = st.text_input("Password Admin", type="password")
    if st.button("Masuk Admin"):
        if admin_pass == "adminsekolah2026": # Password bisa diubah
            st.session_state['logged_in'] = True
            st.session_state['user_role'] = 'admin'
            st.success("Login Admin Berhasil!")
            st.rerun()
        else:
            st.error("Password Salah!")

    if st.session_state.get('user_role') == 'admin':
        st.divider()
        tab1, tab2, tab3 = st.tabs(["Manajemen Siswa", "Input Soal", "Rekap Nilai"])
        
        with tab1:
            st.subheader("Tambah Data Siswa")
            with st.form("form_siswa"):
                k = st.text_input("Kelas (Contoh: 7A, 8B)")
                no = st.number_input("No Absen", min_value=1, step=1)
                nisn = st.text_input("NISN")
                nama = st.text_input("Nama Siswa")
                if st.form_submit_button("Simpan Siswa"):
                    new_row = pd.DataFrame({"Kelas": [k], "No": [no], "NISN": [str(nisn)], "Nama": [nama]})
                    df_siswa = pd.concat([df_siswa, new_row], ignore_index=True)
                    conn.update(worksheet="Siswa", data=df_siswa)
                    st.success(f"Siswa {nama} berhasil disimpan!")
            st.dataframe(df_siswa)

        with tab2:
            st.subheader("Input Soal Ujian")
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
                    new_soal = pd.DataFrame({
                        "Mapel": [m], "KategoriUjian": [kat], "JenisSoal": [jns],
                        "Pertanyaan": [tanya], "OpsiA": [oa], "OpsiB": [ob], "OpsiC": [oc], "OpsiD": [od], "KunciJawaban": [kunci]
                    })
                    df_soal = pd.concat([df_soal, new_soal], ignore_index=True)
                    conn.update(worksheet="Soal", data=df_soal)
                    st.success("Soal berhasil disimpan!")

        with tab3:
            st.subheader("Rekap Nilai Seluruh Siswa")
            st.dataframe(df_nilai)

elif menu == "Login Siswa":
    st.subheader("🎓 Portal Masuk Siswa")
    nisn_input = st.text_input("Masukkan NISN Anda:")
    
    if st.button("Masuk Ujian"):
        cek = df_siswa[df_siswa['NISN'].astype(str) == nisn_input.strip()]
        if not cek.empty:
            st.session_state['logged_in'] = True
            st.session_state['user_role'] = 'siswa'
            st.session_state['user_data'] = cek.iloc[0].to_dict()
            st.success(f"Selamat datang, {st.session_state['user_data']['Nama']}!")
            st.rerun()
        else:
            st.error("NISN tidak ditemukan di database. Hubungi Admin.")

    if st.session_state.get('user_role') == 'siswa':
        siswa = st.session_state['user_data']
        st.info(f"Siswa: **{siswa['Nama']}** | Kelas: **{siswa['Kelas']}**")
        
        mp = st.selectbox("Pilih Mata Pelajaran", [
            "Akidah Akhlak", "Al-Quran Hadits", "Fiqih", "Sejarah Kebudayaan Islam (SKI)",
            "Pendidikan Pancasila", "Bahasa Indonesia", "Ilmu Pengetahuan Alam dan Sosial (IPAS)",
            "Matematika", "Pendidikan Jasmani Olahraga dan Kesehatan (PJOK)",
            "Seni Budaya dan Prakarya (SBdP)", "Bahasa Arab", "Bahasa Sunda",
            "Bahasa Inggris", "Koding dan Kecerdasan Artifisial (KKA)"
        ])
        kp = st.selectbox("Pilih Kategori Ujian", ["Soal Latihan", "Soal Tengah Semester 1", "Soal Tengah Semester 2", "Soal Semester 1", "Soal Semester 2"])
        
        soal_filter = df_soal[(df_soal['Mapel'] == mp) & (df_soal['KategoriUjian'] == kp)]
        
        if not soal_filter.empty:
            with st.form("kerjakan_ujian"):
                ans = {}
                score = 0
                total = len(soal_filter)
                
                for idx, row in soal_filter.iterrows():
                    st.write(f"**Soal {idx+1}:** {row['Pertanyaan']}")
                    if row['JenisSoal'] == 'Pilihan Ganda':
                        ans[idx] = st.radio(f"Pilihan {idx}", [row['OpsiA'], row['OpsiB'], row['OpsiC'], row['OpsiD']], key=f"s_{idx}")
                    else:
                        ans[idx] = st.text_input(f"Jawaban {idx}", key=f"s_{idx}")
                
                if st.form_submit_button("Kirim Jawaban"):
                    for idx, row in soal_filter.iterrows():
                        if str(ans[idx]).strip().lower() == str(row['KunciJawaban']).strip().lower():
                            score += (100 / total)
                    
                    final_sc = round(score, 2)
                    prd = get_predikat(final_sc)
                    
                    new_n = pd.DataFrame({
                        "NISN": [str(siswa['NISN'])], "Nama": [siswa['Nama']], "Kelas": [siswa['Kelas']],
                        "Mapel": [mp], "KategoriUjian": [kp], "Nilai": [final_sc], "Predikat": [prd]
                    })
                    df_nilai = pd.concat([df_nilai, new_n], ignore_index=True)
                    conn.update(worksheet="Nilai", data=df_nilai)
                    st.success(f"Ujian Selesai! Nilai Anda: {final_sc} (Predikat: {prd})")
        else:
            st.warning("Belum ada soal untuk mata pelajaran ini.")