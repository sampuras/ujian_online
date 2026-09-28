import streamlit as st
import pandas as pd
from datetime import datetime
import io

# Konfigurasi Halaman (sidebar otomatis disembunyikan/collapsed saat awal buka)
fn_config = st.set_page_config(
	page_title="Aplikasi Ujian Online Madrasah", 
	layout="wide",
	initial_sidebar_state="collapsed""
	)

# ==================== KUSTOMISASI CSS & TAMPILAN (UI/UX MODERN) ====================
st.markdown("""
<style>
    /* Styling Tombol/Menu Utama di Tengah */
    .hero-container {
        text-align: center;
        padding: 35px;
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        border-radius: 16px;
        border: 1px solid #cbd5e1;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 30px;
    }
    .hero-title {
        font-size: 32px;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 8px;
    }
    .hero-subtitle {
        font-size: 16px;
        color: #0284c7;
        font-weight: 600;
        margin-top: 12px;
    }

    /* Sidebar Modern & Profesional (Dark Clean Theme) */
    [data-testid="stSidebar"] {
        background-color: #0f172a;
        border-right: 1px solid #334155;
    }
    [data-testid="stSidebar"] * {
        color: #f8fafc !important;
    }
    
    /* Badge Admin Profesional */
    .admin-badge {
        background: linear-gradient(135deg, #2563eb, #1d4ed8);
        color: white;
        padding: 10px 14px;
        border-radius: 10px;
        text-align: center;
        font-weight: 600;
        font-size: 14px;
        letter-spacing: 0.5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ==================== KONFIGURASI LINK GOOGLE SHEETS ====================
SOAL_URL = "MASUKKAN_LINK_SHEET_SOAL_DI_SINI"
ADMIN_URL = "MASUKKAN_LINK_SHEET_ADMIN_DI_SINI"
NILAI_URL = "MASUKKAN_LINK_SHEET_NILAI_DI_SINI"
SISWA_URL = "MASUKKAN_LINK_SHEET_SISWA_DI_SINI"

DAFTAR_MAPEL = [
    "Akidah Akhlak", "Al-Quran Hadits", "Fiqih", "Sejarah Kebudayaan Islam",
    "Pendidikan Pancasila", "Bahasa Indonesia", "Ilmu Pengetahuan dan Sosial (IPAS)",
    "Matematika", "Pendidikan Jasmani Olahraga dan Kesehatan", "Seni Budaya dan Prakarya",
    "Bahasa Sunda", "Bahasa Inggris", "Koding dan Kecerdasan Artifisial (KKA)"
]

DAFTAR_KELAS = ["Kelas 1", "Kelas 2", "Kelas 3", "Kelas 4", "Kelas 5", "Kelas 6"]

# ==================== SIDEBAR (NAVIGASI & LOGIN ADMIN MODERN) ====================
st.sidebar.markdown('<div class="admin-badge">🛡️ PORTAL ADMIN MANAJEMEN</div>', unsafe_allow_html=True)
st.sidebar.title("📌 Menu Navigasi")
menu = st.sidebar.radio("Pilih Menu:", ["Ujian Peserta", "Login Admin"])

# ==================== HALAMAN UJIAN PESERTA ====================
if menu == "Ujian Peserta":
    # Tampilan Tengah yang Diperbesar & Elegan
    st.markdown("""
        <div class="hero-container">
            <div class="hero-title">🌟 RUANG UJIAN ONLINE MADRASAH 🌟</div>
            <p style="color: #64748b; font-size: 15px;">Silakan pilih identitas dan mata pelajaran Anda di bawah ini dengan teliti.</p>
            <div class="hero-subtitle">"Bacalah doa dengan tenang 😊 Tunjukkan semangat terbaikmu!"</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Form Pemilihan Siswa
    col1, col2 = st.columns(2)
    with col1:
        pilih_kelas = st.selectbox("🏫 Pilih Jenjang Kelas Anda:", DAFTAR_KELAS)
    with col2:
        daftar_nama_siswa = ["-- Pilih Nama Anda --"]
        try:
            df_siswa = pd.read_csv(SISWA_URL)
            if 'kelas' in df_siswa.columns and 'nama_siswa' in df_siswa.columns:
                filter_siswa = df_siswa[df_siswa['kelas'].astype(str).str.strip().str.lower() == pilih_kelas.strip().lower()]
                daftar_nama_siswa.extend(filter_siswa['nama_siswa'].astype(str).tolist())
        except:
            pass
            
        nama_peserta = st.selectbox("👤 Pilih Nama Lengkap Anda:", daftar_nama_siswa)
        
    pilih_mapel_ujian = st.selectbox("📚 Pilih Mata Pelajaran Ujian:", DAFTAR_MAPEL)
    
    st.divider()

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
        st.warning("⚠️ Silakan pilih nama lengkap Anda terlebih dahulu pada kotak di atas.")
    elif df_soal.empty:
        st.info(f"ℹ️ Belum ada soal untuk mata pelajaran **{pilih_mapel_ujian}** ({pilih_kelas}).")
    else:
        st.success(f"✨ Bismillah, **{nama_peserta}** ({pilih_kelas}). Selamat mengerjakan ujian **{pilih_mapel_ujian}**!")
        with st.form("form_ujian"):
            jawaban_peserta = {}
            for index, row in df_soal.reset_index(drop=True).iterrows():
                st.markdown(f"**Soal {index+1}: {row['pertanyaan']}**")
                pilihan = [row['opsi_a'], row['opsi_b'], row['opsi_c'], row['opsi_d']]
                jawaban_peserta[index] = st.radio(f"Pilih jawaban soal {index+1}:", pilihan, key=f"soal_{index}")
                st.divider()
                
            submit_ujian = st.form_submit_button("🚀 Selesai & Kirim Jawaban")
            
            if submit_ujian:
                skor = 0
                total_soal = len(df_soal)
                
                for index, row in df_soal.reset_index(drop=True).iterrows():
                    pilihan_map = {row['opsi_a']: 'A', row['opsi_b']: 'B', row['opsi_c']: 'C', row['opsi_d']: 'D'}
                    pilih_huruf = pilihan_map.get(jawaban_peserta[index])
                    if pilih_huruf == str(row['kunci']).strip().upper():
                        skor += (100 / total_soal)
                
                st.success(f"🎉 Alhamdulillaah, Ujian {pilih_mapel_ujian} selesai, {nama_peserta}!")
                st.metric(label="📊 Skor Akhir Anda", value=f"{round(skor, 2)} / 100")

# ==================== HALAMAN LOGIN ADMIN (DI SIDEBAR KIRI) ====================
elif menu == "Login Admin":
    st.sidebar.markdown("### 🔐 Autentikasi Sistem")
    
    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False
        st.session_state.admin_user = ""
        st.session_state.admin_kelas = ""
        
    if not st.session_state.admin_logged_in:
        with st.sidebar.form("form_login"):
            tipe_admin = st.selectbox("Masuk Sebagai:", ["Admin Utama", "Admin Per Kelas"])
            pilihan_kelas_login = ""
            if tipe_admin == "Admin Per Kelas":
                pilihan_kelas_login = st.selectbox("Pilih Kelas Akses:", DAFTAR_KELAS)
                
            u_input = st.text_input("Username")
            p_input = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("Masuk Panel")
            
            if login_btn:
                if tipe_admin == "Admin Utama":
                    if u_input == "admin" and p_input == "123":
                        st.session_state.admin_logged_in = True
                        st.session_state.admin_user = u_input
                        st.session_state.admin_kelas = "Semua"
                        st.rerun()
                    else:
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
                                st.error("Username/Password Admin Utama Salah!")
                        except:
                            st.error("Gagal verifikasi data admin.")
                else:
                    st.session_state.admin_logged_in = True
                    st.session_state.admin_user = u_input if u_input else f"Guru_{pilihan_kelas_login}"
                    st.session_state.admin_kelas = pilihan_kelas_login
                    st.rerun()
    else:
        # Tampilan Dashboard Utama setelah Admin Masuk
        st.title("📊 Dashboard Panel Admin")
        st.success(f"Selamat datang, **{st.session_state.admin_user}**! Hak Akses Kelas: **{st.session_state.admin_kelas}**")
        
        tab1, tab2, tab3, tab4 = st.tabs(["➕ Input Soal", "👥 Daftar Siswa", "📊 Rekap Nilai", "⚙️ Info Akun"])
        
        with tab1:
            st.subheader("Input Soal & Kunci Jawaban")
            if st.session_state.admin_kelas.lower() in ["semua", "all", "admin utama"]:
                kelas_input = st.selectbox("Pilih Jenjang Kelas:", DAFTAR_KELAS, key="input_kelas_admin")
            else:
                kelas_input = st.session_state.admin_kelas
                st.info(f"🔒 Mengelola soal khusus untuk: **{kelas_input}**")
                
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
                    st.info(f"Salin teks di bawah ini dan tempelkan ke baris baru di Google Sheet soal:")
                    format_teks = f"kelas: {kelas_input} | mapel: {mapel_input} | pertanyaan: {pertanyaan} | opsi_a: {opsi_a} | opsi_b: {opsi_b} | opsi_c: {opsi_c} | opsi_d: {opsi_d} | kunci: {kunci}"
                    st.code(format_teks)
                    st.success("Format siap disalin!")

        with tab2:
            st.subheader("Daftar Siswa Terdaftar")
            try:
                df_siswa_view = pd.read_csv(SISWA_URL)
                if not (st.session_state.admin_kelas.lower() in ["semua", "all", "admin utama"]):
                    if 'kelas' in df_siswa_view.columns:
                        df_siswa_view = df_siswa_view[df_siswa_view['kelas'].astype(str).str.strip().str.lower() == st.session_state.admin_kelas.strip().lower()]
                st.dataframe(df_siswa_view, use_container_width=True)
            except:
                st.info("Belum ada data siswa atau link Google Sheet belum diatur.")

        with tab3:
            st.subheader("Rekap Nilai Siswa")
            try:
                df_nilai = pd.read_csv(NILAI_URL)
                if not (st.session_state.admin_kelas.lower() in ["semua", "all", "admin utama"]):
                    if 'kelas' in df_nilai.columns:
                        df_nilai = df_nilai[df_nilai['kelas'].astype(str).str.strip().str.lower() == st.session_state.admin_kelas.strip().lower()]
                st.dataframe(df_nilai, use_container_width=True)
            except:
                st.info("Belum ada data nilai tersimpan.")
            
        with tab4:
            st.subheader("Pengaturan Sesi")
            st.write(f"Akun aktif: **{st.session_state.admin_user}**")
            st.write(f"Hak akses kelas: **{st.session_state.admin_kelas}**")
                    
        if st.sidebar.button("Keluar (Logout Admin)"):
            st.session_state.admin_logged_in = False
            st.session_state.admin_user = ""
            st.session_state.admin_kelas = ""
            st.rerun()
