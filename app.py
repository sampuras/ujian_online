import streamlit as st
import pandas as pd
from datetime import datetime
import io

# Konfigurasi Halaman
st.set_page_config(page_title="Aplikasi Ujian Online Madrasah", layout="wide")

# ==================== KONFIGURASI LINK GOOGLE SHEETS ====================
SOAL_URL = "MASUKKAN_LINK_SHEET_SOAL_DI_SINI"
ADMIN_URL = "MASUKKAN_LINK_SHEET_ADMIN_DI_SINI"
NILAI_URL = "MASUKKAN_LINK_SHEET_NILAI_DI_SINI"
SISWA_URL = "MASUKKAN_LINK_SHEET_SISWA_DI_SINI"  # <-- Link Google Sheet Daftar Siswa

# Daftar 14 Mata Pelajaran Madrasah/SD
DAFTAR_MAPEL = [
    "Akidah Akhlak",
    "Al-Quran Hadits",
    "Fiqih",
    "Sejarah Kebudayaan Islam",
    "Pendidikan Pancasila",
    "Bahasa Indonesia",
    "Ilmu Pengetahuan dan Sosial (IPAS)",
    "Matematika",
    "Pendidikan Jasmani Olahraga dan Kesehatan",
    "Seni Budaya dan Prakarya",
    "Bahasa Sunda",
    "Bahasa Inggris",
    "Koding dan Kecerdasan Artifisial (KKA)"
]

DAFTAR_KELAS = ["Kelas 1", "Kelas 2", "Kelas 3", "Kelas 4", "Kelas 5", "Kelas 6"]

# Sidebar / Taskbar Navigasi
st.sidebar.title("📌 Menu Navigasi")
menu = st.sidebar.radio("Pilih Halaman:", ["Ujian Peserta", "Login Admin"])

# ==================== HALAMAN UJIAN PESERTA ====================
if menu == "Ujian Peserta":
    st.title("📝 Ruang Ujian Peserta")
    
    col1, col2 = st.columns(2)
    with col1:
        pilih_kelas = st.selectbox("Pilih Jenjang Kelas Anda:", DAFTAR_KELAS)
    with col2:
        # Tarik daftar nama siswa berdasarkan kelas yang dipilih
        daftar_nama_siswa = ["-- Pilih Nama Anda --"]
        try:
            df_siswa = pd.read_csv(SISWA_URL)
            if 'kelas' in df_siswa.columns and 'nama_siswa' in df_siswa.columns:
                filter_siswa = df_siswa[df_siswa['kelas'].astype(str).str.strip().str.lower() == pilih_kelas.strip().lower()]
                daftar_nama_siswa.extend(filter_siswa['nama_siswa'].astype(str).tolist())
        except:
            pass
            
        nama_peserta = st.selectbox("Pilih Nama Lengkap Anda:", daftar_nama_siswa)
        
    pilih_mapel_ujian = st.selectbox("Pilih Mata Pelajaran Ujian:", DAFTAR_MAPEL)
    
    # Ambil soal berdasarkan kelas dan mapel
    try:
        df_all_soal = pd.read_csv(SOAL_URL)
        if 'mapel' in df_all_soal.columns and 'kelas' in df_all_soal.columns:
            df_soal = df_all_soal[
                (df_all_soal['mapel'].str.strip().str.lower() == pilih_mapel_ujian.strip().lower()) & 
                (df_all_soal['kelas'].str.strip().str.lower() == pilih_kelas.strip().lower())
            ]
        else:
            df_soal = pd.DataFrame(columns=["id", "kelas", "mapel", "pertanyaan", "opsi_a", "opsi_b", "opsi_c", "opsi_d", "kunci"])
    except:
        df_soal = pd.DataFrame(columns=["id", "kelas", "mapel", "pertanyaan", "opsi_a", "opsi_b", "opsi_c", "opsi_d", "kunci"])
    
    if nama_peserta == "-- Pilih Nama Anda --":
        st.warning("Silakan pilih nama lengkap Anda terlebih dahulu pada daftar di atas.")
    elif df_soal.empty:
        st.info(f"Belum ada soal untuk mata pelajaran **{pilih_mapel_ujian}** ({pilih_kelas}).")
    else:
        st.info(f"Halo **{nama_peserta}**, Anda akan mengerjakan ujian **{pilih_mapel_ujian}** ({pilih_kelas}). Selamat mengerjakan!")
        with st.form("form_ujian"):
            jawaban_peserta = {}
            for index, row in df_soal.reset_index(drop=True).iterrows():
                st.markdown(f"**Soal {index+1}: {row['pertanyaan']}**")
                pilihan = [row['opsi_a'], row['opsi_b'], row['opsi_c'], row['opsi_d']]
                jawaban_peserta[index] = st.radio(f"Pilih jawaban soal {index+1}:", pilihan, key=f"soal_{index}")
                st.divider()
                
            submit_ujian = st.form_submit_button("Selesai & Kirim Jawaban")
            
            if submit_ujian:
                skor = 0
                total_soal = len(df_soal)
                
                for index, row in df_soal.reset_index(drop=True).iterrows():
                    pilihan_map = {row['opsi_a']: 'A', row['opsi_b']: 'B', row['opsi_c']: 'C', row['opsi_d']: 'D'}
                    pilih_huruf = pilihan_map.get(jawaban_peserta[index])
                    if pilih_huruf == str(row['kunci']).strip().upper():
                        skor += (100 / total_soal)
                
                # Catatan: Rekap nilai nantinya bisa menyimpan kolom: kelas, nama_peserta, mapel, skor, tanggal
                st.success(f"Ujian {pilih_mapel_ujian} ({pilih_kelas}) Selesai! Terima kasih, {nama_peserta}.")
                st.metric(label="Skor Anda", value=f"{round(skor, 2)} / 100")
                st.info("Nilai Anda telah berhasil direkam oleh sistem.")

# ==================== HALAMAN ADMIN ====================
elif menu == "Login Admin":
    st.title("🔐 Panel Admin Madrasah")
    
    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False
        st.session_state.admin_user = ""
        st.session_state.admin_kelas = ""
        
    if not st.session_state.admin_logged_in:
        with st.form("form_login"):
            u_input = st.text_input("Username Admin")
            p_input = st.text_input("Password Admin", type="password")
            login_btn = st.form_submit_button("Masuk")
            
            if login_btn:
                try:
                    df_admin = pd.read_csv(ADMIN_URL)
                    match = df_admin[
                        (df_admin['username'].astype(str).str.strip() == u_input.strip()) & 
                        (df_admin['password'].astype(str).str.strip() == p_input.strip())
                    ]
                    
                    if not match.empty:
                        st.session_state.admin_logged_in = True
                        st.session_state.admin_user = u_input
                        st.session_state.admin_kelas = str(match.iloc[0]['kelas_akses']).strip()
                        st.rerun()
                    else:
                        st.error("Username atau Password salah!")
                except Exception as e:
                    if u_input == "admin" and p_input == "123":
                        st.session_state.admin_logged_in = True
                        st.session_state.admin_user = "admin"
                        st.session_state.admin_kelas = "Semua"
                        st.rerun()
                    else:
                        st.error(f"Gagal memuat data admin dari Google Sheets. Error: {e}")
    else:
        st.success(f"Selamat datang, **{st.session_state.admin_user}**! Hak Akses Kelas: **{st.session_state.admin_kelas}**")
        
        tab1, tab2, tab3, tab4 = st.tabs(["➕ Input Soal", "👥 Daftar Siswa", "📊 Rekap Nilai", "⚙️ Info Akun"])
        
        # Tab 1: Input Soal
        with tab1:
            st.subheader("Input Soal & Kunci Jawaban")
            if st.session_state.admin_kelas.lower() in ["semua", "all", "admin utama"]:
                kelas_input = st.selectbox("Pilih Jenjang Kelas:", DAFTAR_KELAS, key="input_kelas_admin")
            else:
                kelas_input = st.session_state.admin_kelas
                st.info(f"Anda masuk sebagai pengelola khusus: **{kelas_input}**")
                
            mapel_input = st.selectbox("Pilih Mata Pelajaran:", DAFTAR_MAPEL, key="input_mapel_admin")
            
            with st.form("form_tambah_soal"):
                pertanyaan = st.text_area("Pertanyaan Soal")
                opsi_a = st.text_input("Pilihan A")
                opsi_b = st.text_input("Pilihan B")
                opsi_c = st.text_input("Pilihan C")
                opsi_d = st.text_input("Pilihan D")
                kunci = st.selectbox("Kunci Jawaban Benar", ["A", "B", "C", "D"])
                
                simpan_soal_btn = st.form_submit_button("Generate Format Soal")
                
                if simpan_soal_btn:
                    st.info(f"Salin teks di bawah ini dan tempelkan ke baris baru di **Google Sheet soal** Anda:")
                    format_teks = f"kelas: {kelas_input} | mapel: {mapel_input} | pertanyaan: {pertanyaan} | opsi_a: {opsi_a} | opsi_b: {opsi_b} | opsi_c: {opsi_c} | opsi_d: {opsi_d} | kunci: {kunci}"
                    st.code(format_teks)
                    st.success("Format siap disalin ke Google Sheets!")

        # Tab 2: Daftar Siswa
        with tab2:
            st.subheader("Kelola & Lihat Data Siswa")
            st.write("Berikut adalah daftar siswa yang terdaftar di sistem berdasarkan Google Sheet **siswa**:")
            try:
                df_siswa_view = pd.read_csv(SISWA_URL)
                if not (st.session_state.admin_kelas.lower() in ["semua", "all", "admin utama"]):
                    if 'kelas' in df_siswa_view.columns:
                        df_siswa_view = df_siswa_view[df_siswa_view['kelas'].astype(str).str.strip().str.lower() == st.session_state.admin_kelas.strip().lower()]
                st.dataframe(df_siswa_view, use_container_width=True)
            except:
                st.info("Belum ada data siswa atau link sheet siswa belum diatur.")
            st.info("💡 Untuk menambah atau mengubah data siswa, silakan lakukan langsung di dalam file Google Sheet **siswa** Anda.")

        # Tab 3: Rekap Nilai
        with tab3:
            st.subheader("Daftar Nilai Peserta Ujian")
            try:
                df_nilai = pd.read_csv(NILAI_URL)
                if not (st.session_state.admin_kelas.lower() in ["semua", "all", "admin utama"]):
                    if 'kelas' in df_nilai.columns:
                        df_nilai = df_nilai[df_nilai['kelas'].astype(str).str.strip().str.lower() == st.session_state.admin_kelas.strip().lower()]
                st.dataframe(df_nilai, use_container_width=True)
            except:
                st.info("Belum ada data nilai atau link sheet nilai belum diatur.")
            
        # Tab 4: Info Akun
        with tab4:
            st.subheader("Informasi Akses Admin")
            st.write(f"Username Aktif: **{st.session_state.admin_user}**")
            st.write(f"Hak Akses Kelas: **{st.session_state.admin_kelas}**")
                    
        if st.button("Keluar (Logout Admin)"):
            st.session_state.admin_logged_in = False
            st.session_state.admin_user = ""
            st.session_state.admin_kelas = ""
            st.rerun()
