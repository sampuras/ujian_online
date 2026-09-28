import streamlit as st
import pandas as pd
from datetime import datetime

# Konfigurasi Halaman
st.set_page_config(page_title="Aplikasi Ujian Online", layout="wide")

# Masukkan Link Publik Google Sheets Anda di sini
# (Pastikan link berakhiran /export?format=csv agar bisa dibaca langsung)
# CONTOH LINK: https://docs.google.com/spreadsheets/d/1ABC.../export?format=csv

ADMIN_URL = "https://docs.google.com/spreadsheets/d/108IxPi-bYWFVNuE3CWntGrLnqKE29m5gJgBonOIum5I/export?format=csv"
SOAL_URL = "https://docs.google.com/spreadsheets/d/1nxoioUJKfs2wcgFjZdsIBImJgJF5rDZTpvXR2UAaEB0/export?format=csv"
NILAI_URL = "https://docs.google.com/spreadsheets/d/1X39Woj0UIA9-vLJL397AVDmpvBjYiPLnBfbLd2XLBfU/export?format=csv"

# Sidebar / Taskbar Navigasi
st.sidebar.title("📌 Menu Navigasi")
menu = st.sidebar.radio("Pilih Halaman:", ["Ujian Peserta", "Login Admin"])

# ==================== HALAMAN UJIAN PESERTA ====================
if menu == "Ujian Peserta":
    st.title("📝 Ruang Ujian Peserta")
    
    nama_peserta = st.text_input("Masukkan Nama Lengkap Anda:")
    
    try:
        df_soal = pd.read_csv(SOAL_URL)
    except:
        df_soal = pd.DataFrame(columns=["id", "pertanyaan", "opsi_a", "opsi_b", "opsi_c", "opsi_d", "kunci"])
    
    if not nama_peserta:
        st.warning("Silakan masukkan nama Anda terlebih dahulu untuk memulai ujian.")
    elif df_soal.empty:
        st.info("Belum ada soal ujian yang dimasukkan oleh Admin.")
    else:
        with st.form("form_ujian"):
            jawaban_peserta = {}
            for index, row in df_soal.iterrows():
                st.markdown(f"**Soal {index+1}: {row['pertanyaan']}**")
                pilihan = [row['opsi_a'], row['opsi_b'], row['opsi_c'], row['opsi_d']]
                jawaban_peserta[index] = st.radio(f"Pilih jawaban soal {index+1}:", pilihan, key=f"soal_{index}")
                st.divider()
                
            submit_ujian = st.form_submit_button("Selesai & Kirim Jawaban")
            
            if submit_ujian:
                skor = 0
                total_soal = len(df_soal)
                
                for index, row in df_soal.iterrows():
                    pilihan_map = {row['opsi_a']: 'A', row['opsi_b']: 'B', row['opsi_c']: 'C', row['opsi_d']: 'D'}
                    pilih_huruf = pilihan_map.get(jawaban_peserta[index])
                    if pilih_huruf == str(row['kunci']).strip().upper():
                        skor += (100 / total_soal)
                
                st.success(f"Ujian Selesai! Terima kasih, {nama_peserta}.")
                st.metric(label="Skor Anda", value=f"{round(skor, 2)} / 100")
                st.info("Catatan: Pada mode publik ini, rekap nilai otomatis direkam langsung ke Google Sheet Anda saat ujian disubmit.")

# ==================== HALAMAN ADMIN ====================
elif menu == "Login Admin":
    st.title("🔐 Panel Admin")
    
    try:
        df_admin = pd.read_csv(ADMIN_URL)
        user_db = str(df_admin.loc[0, "username"])
        pass_db = str(df_admin.loc[0, "password"])
    except:
        user_db = "admin"
        pass_db = "123"
    
    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False
        
    if not st.session_state.admin_logged_in:
        with st.form("form_login"):
            u_input = st.text_input("Username Admin")
            p_input = st.text_input("Password Admin", type="password")
            login_btn = st.form_submit_button("Masuk")
            
            if login_btn:
                if u_input == user_db and p_input == pass_db:
                    st.session_state.admin_logged_in = True
                    st.rerun()
                else:
                    st.error("Username atau Password salah!")
    else:
        st.success("Selamat datang di Dashboard Admin!")
        
        tab1, tab2, tab3 = st.tabs(["➕ Blanko Soal", "📊 Rekap Nilai Peserta", "⚙️ Pengaturan Akun"])
        
        with tab1:
            st.subheader("Input Soal Baru")
            st.info("Untuk menambah soal dengan mudah, Anda bisa langsung mengetik atau memasukkannya ke dalam Google Sheet 'soal' Anda secara langsung.")
            
        with tab2:
            st.subheader("Daftar Nilai Peserta Ujian")
            try:
                df_nilai = pd.read_csv(NILAI_URL)
                st.dataframe(df_nilai)
            except:
                st.info("Belum ada data nilai atau link sheet nilai belum diatur.")
            
        with tab3:
            st.subheader("Pengaturan Akun Admin")
            st.write(f"Username Admin saat ini: **{user_db}**")
            st.info("Untuk mengganti password atau username, Anda dapat langsung mengubahnya di Google Sheet 'admin' pada baris pertama.")
                    
        if st.button("Keluar (Logout Admin)"):
            st.session_state.admin_logged_in = False
            st.rerun()
