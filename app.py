import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Konfigurasi Halaman
st.set_page_config(page_title="Aplikasi Ujian Online", layout="wide")

# Inisialisasi Database Excel jika belum ada
if not os.path.exists("admin.xlsx"):
    pd.DataFrame({"username": ["admin"], "password": ["123"]}).to_excel("admin.xlsx", index=False)
if not os.path.exists("soal.xlsx"):
    pd.DataFrame(columns=["id", "pertanyaan", "opsi_a", "opsi_b", "opsi_c", "opsi_d", "kunci"]).to_excel("soal.xlsx", index=False)
if not os.path.exists("nilai.xlsx"):
    pd.DataFrame(columns=["nama_peserta", "skor", "tanggal"]).to_excel("nilai.xlsx", index=False)

# Sidebar / Taskbar Navigasi
st.sidebar.title("📌 Menu Navigasi")
menu = st.sidebar.radio("Pilih Halaman:", ["Ujian Peserta", "Login Admin"])

# ==================== HALAMAN UJIAN PESERTA ====================
if menu == "Ujian Peserta":
    st.title("📝 Ruang Ujian Peserta")
    
    nama_peserta = st.text_input("Masukkan Nama Lengkap Anda:")
    
    df_soal = pd.read_excel("soal.xlsx")
    
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
                
                df_nilai = pd.read_excel("nilai.xlsx")
                new_row = {"nama_peserta": nama_peserta, "skor": round(skor, 2), "tanggal": datetime.now().strftime("%Y-%m-%d %H:%M")}
                df_nilai = pd.concat([df_nilai, pd.DataFrame([new_row])], ignore_index=True)
                df_nilai.to_excel("nilai.xlsx", index=False)
                
                st.success(f"Ujian Selesai! Terima kasih, {nama_peserta}.")
                st.metric(label="Skor Anda", value=f"{round(skor, 2)} / 100")

# ==================== HALAMAN ADMIN ====================
elif menu == "Login Admin":
    st.title("🔐 Panel Admin")
    
    df_admin = pd.read_excel("admin.xlsx")
    user_db = df_admin.loc[0, "username"]
    pass_db = str(df_admin.loc[0, "password"])
    
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
            st.subheader("Input Soal dan Kunci Jawaban")
            with st.form("form_soal"):
                pertanyaan = st.text_area("Pertanyaan Soal")
                opsi_a = st.text_input("Pilihan A")
                opsi_b = st.text_input("Pilihan B")
                opsi_c = st.text_input("Pilihan C")
                opsi_d = st.text_input("Pilihan D")
                kunci = st.selectbox("Kunci Jawaban Benar", ["A", "B", "C", "D"])
                
                simpan_soal = st.form_submit_button("Simpan Soal ke Excel")
                if simpan_soal:
                    df_soal = pd.read_excel("soal.xlsx")
                    new_id = len(df_soal) + 1
                    new_soal = {
                        "id": new_id, "pertanyaan": pertanyaan, 
                        "opsi_a": opsi_a, "opsi_b": opsi_b, 
                        "opsi_c": opsi_c, "opsi_d": opsi_d, "kunci": kunci
                    }
                    df_soal = pd.concat([df_soal, pd.DataFrame([new_soal])], ignore_index=True)
                    df_soal.to_excel("soal.xlsx", index=False)
                    st.success("Soal berhasil ditambahkan ke database Excel!")
                    
        with tab2:
            st.subheader("Daftar Nilai Peserta Ujian")
            df_nilai = pd.read_excel("nilai.xlsx")
            st.dataframe(df_nilai)
            
        with tab3:
            st.subheader("Ganti Username & Password Admin")
            with st.form("form_ganti_akun"):
                new_user = st.text_input("Username Baru", value=user_db)
                new_pass = st.text_input("Password Baru", type="password")
                update_btn = st.form_submit_button("Perbarui Akun")
                
                if update_btn:
                    df_admin.loc[0, "username"] = new_user
                    df_admin.loc[0, "password"] = new_pass
                    df_admin.to_excel("admin.xlsx", index=False)
                    st.success("Akun admin berhasil diperbarui!")
                    
        if st.button("Keluar (Logout Admin)"):
            st.session_state.admin_logged_in = False
            st.rerun()
