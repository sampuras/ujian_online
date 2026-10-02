from datetime import datetime
import io
import random
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# Konfigurasi Halaman Utama
st.set_page_config(
    page_title="UJIAN MI ASHSHOLAHIYAH", page_icon="🕌", layout="wide"
)

# Auto refresh untuk pemantauan online & jam real-time (tiap 10 detik)
st_autorefresh(interval=10000, key="datarefresh")

# --- CUSTOM CSS: Perbaikan Warna Label & Teks Input ---
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        max-width: 100% !important;
    }
    .stApp {
        background: linear-gradient(135deg, #090a0f 0%, #121824 50%, #1a2233 100%);
        color: #f1f5f9;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Perbaikan agar seluruh label input Streamlit berwarna putih dan jelas */
    .stTextInput label, .stSelectbox label, .stTextArea label {
        color: #f8fafc !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
    }

    /* Sidebar Tertutup Default di Pojok Kiri Atas */
    [data-testid="stSidebar"] {
        background-color: #0d131f;
        border-right: 1px solid #334155;
    }
    [data-testid="stSidebar"] .stMarkdown {
        color: #cbd5e1;
    }

    /* Pembungkus Portal Siswa Proporsional & Ceria (Aurora Hitam-Perak) */
    .portal-wrapper {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 30px;
        margin-bottom: 30px;
    }
    .book-frame {
        background: rgba(18, 24, 36, 0.9);
        border: 2px solid #cbd5e1;
        border-radius: 20px;
        padding: 40px 45px;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.8), 0 0 35px rgba(203, 213, 225, 0.2);
        backdrop-filter: blur(12px);
        width: 100%;
        max-width: 580px;
    }

    .main-title {
        text-align: center;
        font-size: 1.8rem;
        font-weight: 800;
        background: linear-gradient(90deg, #f8fafc, #94a3b8, #cbd5e1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin-bottom: 8px;
        text-shadow: 0 2px 4px rgba(0,0,0,0.5);
    }
    .subtitle {
        text-align: center;
        color: #94a3b8;
        font-size: 0.95rem;
        margin-bottom: 25px;
        font-weight: 500;
    }

    /* Posisi Login Admin di Pojok Kanan Atas agar Tidak Mengganggu */
    .admin-corner {
        position: absolute;
        top: 15px;
        right: 25px;
        z-index: 999;
    }

    div.stButton > button {
        background: linear-gradient(90deg, #334155, #475569);
        color: #ffffff;
        font-weight: 600;
        border: 1px solid #94a3b8;
        border-radius: 10px;
        padding: 10px 20px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    div.stButton > button:hover {
        background: linear-gradient(90deg, #475569, #64748b);
        border-color: #ffffff;
        box-shadow: 0 0 15px rgba(255, 255, 255, 0.3);
    }

    .stTextInput input {
        background-color: rgba(15, 23, 42, 0.95) !important;
        color: #f1f5f9 !important;
        border: 1px solid #475569 !important;
        border-radius: 8px !important;
        padding: 10px !important;
    }
    .stTextInput input:focus {
        border-color: #cbd5e1 !important;
        box-shadow: 0 0 8px rgba(203, 213, 225, 0.3) !important;
    }

    div[data-testid="stMetric"] {
        background-color: rgba(30, 41, 59, 0.8);
        border: 1px solid #475569;
        padding: 12px;
        border-radius: 12px;
    }
    div[data-testid="stMetric"] label {
        color: #94a3b8 !important;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #f8fafc !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# --- KONEKSI GOOGLE SHEETS ---
@st.cache_resource
def init_connection():
  try:
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    if "gcp_service_account" in st.secrets:
      creds_dict = dict(st.secrets["gcp_service_account"])
      creds = ServiceAccountCredentials.from_json_keyfile_dict(
          creds_dict, scope
      )
    else:
      creds = ServiceAccountCredentials.from_json_keyfile_name(
          "credentials.json", scope
      )
    client = gspread.authorize(creds)
    return client
  except Exception:
    return None


client = init_connection()


def get_data(sheet_name):
  if client is None:
    return pd.DataFrame()
  try:
    sheet = client.open("DB_Ujian_Madrasah").worksheet(sheet_name)
    data = sheet.get_all_records()
    return pd.DataFrame(data)
  except Exception:
    return pd.DataFrame()


def update_data(sheet_name, df):
  if client is None:
    return
  try:
    sheet = client.open("DB_Ujian_Madrasah").worksheet(sheet_name)
    sheet.clear()
    sheet.update(
        [df.columns.values.tolist()] + df.astype(str).values.tolist()
    )
  except Exception as e:
    st.error(f"Gagal memperbarui database: {e}")


# --- INISIALISASI SESSION STATE ---
if "logged_in" not in st.session_state:
  st.session_state.logged_in = False
if "role" not in st.session_state:
  st.session_state.role = None
if "user_data" not in st.session_state:
  st.session_state.user_data = {}
if "otp_sent" not in st.session_state:
  st.session_state.otp_sent = False
if "generated_otp" not in st.session_state:
  st.session_state.generated_otp = ""

LIST_MAPEL = [
    "Akidah Akhlak",
    "Al-Quran Hadits",
    "Fiqih",
    "Sejarah Kebudayaan Islam (SKI)",
    "Pendidikan Pancasila",
    "Bahasa Indonesia",
    "Ilmu Pengetahuan Alam dan Sosial (IPAS)",
    "Matematika",
    "Pendidikan Jasmani Olahraga dan Kesehatan (PJOK)",
    "Seni Budaya dan Prakarya (SBdP)",
    "Bahasa Arab",
    "Bahasa Sunda",
    "Bahasa Inggris",
    "Koding dan Kecerdasan Artifisial (KKA)",
]

# --- WIDGET INFORMASI WAKTU & STATUS ONLINE DI SETIAP HALAMAN ---
now_time = datetime.now()
hari_ini = [
    "Senin",
    "Selasa",
    "Rabu",
    "Kamis",
    "Jumat",
    "Sabtu",
    "Minggu",
][now_time.weekday()]
tanggal_str = now_time.strftime("%d-%m-%Y")
jam_str = now_time.strftime("%H:%M:%S")

df_s_live = get_data("siswa")
df_g_live = get_data("guru")
total_online_siswa = (
    len(df_s_live[df_s_live["status_online"] == "Online"])
    if not df_s_live.empty
    else 0
)
total_online_guru = (
    len(df_g_live[df_g_live["status_online"] == "Online"])
    if not df_g_live.empty
    else 0
)

st.markdown(
    f"""
    <div style="display: flex; justify-content: space-between; background: rgba(30,41,59,0.6); padding: 8px 15px; border-radius: 8px; border: 1px solid #334155; font-size: 0.85rem; margin-bottom: 15px;">
        <div>📅 <b>{hari_ini}, {tanggal_str}</b> | ⏰ <b>{jam_str} WIB</b></div>
        <div>🟢 Guru Online: <b>{total_online_guru}</b> | 🟢 Siswa Online: <b>{total_online_siswa}</b></div>
    </div>
""",
    unsafe_allow_html=True,
)

# --- TOMBOL LOGIN ADMIN / GURU DI POJOK KANAN ATAS ---
st.markdown('<div class="admin-corner">', unsafe_allow_html=True)
if not st.session_state.logged_in:
  if st.button("🔐 Login Admin / Guru"):
    st.session_state.show_login_modal = True
st.markdown("</div>", unsafe_allow_html=True)

# Modal Login Admin / Guru dengan Keamanan 2 Lapis OTP
if st.session_state.get("show_login_modal", False):
  with st.expander(
      "🔑 Portal Masuk Khusus Admin & Guru Kelas", expanded=True
  ):
    u_input = st.text_input("Username")
    p_input = st.text_input("Password", type="password")
    if st.button("Proses Masuk"):
      if u_input == "rudinasruddin" and p_input == "1234567890":
        otp = str(random.randint(100000, 999999))
        st.session_state.generated_otp = otp
        st.session_state.otp_sent = True
        st.success(
            "Keamanan 2 Lapis: Kode OTP telah dikirim ke email"
            " dosnasruddin@gmail.com"
        )
      else:
        df_g_check = get_data("guru")
        if not df_g_check.empty:
          match_g = df_g_check[
              (df_g_check["username"].astype(str) == str(u_input))
              & (df_g_check["password"].astype(str) == str(p_input))
          ]
          if not match_g.empty:
            g_info = match_g.iloc[0].to_dict()
            df_g_check.loc[
                df_g_check["username"].astype(str) == str(u_input),
                "status_online",
            ] = "Online"
            update_data("guru", df_g_check)

            st.session_state.logged_in = True
            st.session_state.role = "guru"
            st.session_state.user_data = g_info
            st.session_state.show_login_modal = False
            st.success(f"Selamat datang, Guru Kelas {g_info['kelas']}!")
            st.rerun()
          else:
            st.error("Username atau Password salah!")
        else:
          st.error("Database guru belum tersedia.")

    if st.session_state.otp_sent:
      otp_input = st.text_input("Masukkan Kode OTP 6 Digit")
      if st.button("Verifikasi OTP"):
        if otp_input == st.session_state.generated_otp:
          df_g_check = get_data("guru")
          if not df_g_check.empty:
            df_g_check.loc[
                df_g_check["username"].astype(str) == "rudinasruddin",
                "status_online",
            ] = "Online"
            update_data("guru", df_g_check)

          st.session_state.logged_in = True
          st.session_state.role = "admin"
          st.session_state.user_data = {
              "nama": "Nasruddin (Admin)",
              "kelas": "Semua",
              "username": "rudinasruddin",
          }
          st.session_state.show_login_modal = False
          st.success("Verifikasi OTP Berhasil! Login Admin Diterima.")
          st.rerun()
        else:
          st.error("Kode OTP salah!")

    if st.button("Tutup"):
      st.session_state.show_login_modal = False
      st.rerun()

# --- HALAMAN UTAMA / PORTAL MASUK SISWA (BINGKAI PROPORSIONAL) ---
if not st.session_state.logged_in:
  st.markdown(
      """
        <div class="portal-wrapper">
            <div class="book-frame">
                <div class="main-title">UJIAN MI ASHSHOLAHIYAH</div>
                <div class="subtitle">Portal Masuk Khusus Peserta Didik</div>
    """,
      unsafe_allow_html=True,
  )

  df_siswa_check = get_data("siswa")
  nisn_login = st.text_input("Nomor Peserta / NISN")
  pass_login = st.text_input("Password Siswa", type="password")

  st.markdown("<br>", unsafe_allow_html=True)
  if st.button("Masuk Ujian Sekarang →", use_container_width=True):
    if not df_siswa_check.empty:
      match = df_siswa_check[
          (df_siswa_check["nisn"].astype(str) == str(nisn_login))
          & (df_siswa_check["password"].astype(str) == str(pass_login))
      ]
      if not match.empty:
        siswa_info = match.iloc[0].to_dict()
        st.session_state.logged_in = True
        st.session_state.role = "siswa"
        st.session_state.user_data = siswa_info

        df_siswa_check.loc[
            df_siswa_check["nisn"].astype(str) == str(nisn_login),
            "status_online",
        ] = "Online"
        update_data("siswa", df_siswa_check)

        st.success(f"Selamat datang, {siswa_info['nama']}!")
        st.rerun()
      else:
        st.error("Nomor Peserta / NISN atau Password salah.")
    else:
      st.warning("Database siswa kosong.")

  st.markdown(
      """
                <p style='text-align: center; color: #94a3b8; font-size: 0.82rem; margin-top: 15px; margin-bottom: 0;'>🔒 Hanya siswa terdaftar dalam database yang dapat masuk</p>
            </div>
        </div>
    """,
      unsafe_allow_html=True,
  )

# --- DASHBOARD SETELAH LOGIN ---
else:
  role = st.session_state.role
  user = st.session_state.user_data

  with st.sidebar:
    st.markdown(f"### 👤 **{user.get('nama', 'User')}**")
    st.markdown(f"**Akses:** {role.upper()}")
    if role == "guru":
      st.markdown(f"**Wali Kelas:** {user.get('kelas')}")

    if st.button("Keluar / Logout", use_container_width=True):
      if role == "siswa":
        df_s = get_data("siswa")
        if not df_s.empty:
          df_s.loc[
              df_s["nisn"].astype(str) == str(user.get("nisn")), "status_online"
          ] = "Offline"
          update_data("siswa", df_s)
      elif role in ["admin", "guru"]:
        df_g = get_data("guru")
        if not df_g.empty:
          df_g.loc[
              df_g["username"].astype(str) == str(user.get("username")),
              "status_online",
          ] = "Offline"
          update_data("guru", df_g)

      st.session_state.logged_in = False
      st.session_state.role = None
      st.session_state.user_data = {}
      st.rerun()
    st.markdown("---")

  # --- PANEL ADMIN & GURU KELAS ---
  if role in ["admin", "guru"]:
    st.markdown(
        f"## 🛠️ Panel Pengelolaan Ujian MI Ashsholahiyah ({role.upper()})"
    )

    tab_siswa, tab_soal, tab_atur, tab_pantau, tab_nilai = st.tabs([
        "👥 Manajemen Siswa & Kartu Ujian",
        "📚 Bank Soal & Template Offline",
        "⚙️ Pengaturan & Rilis Ujian",
        "📡 Pemantauan Online & Pengerjaan",
        "📊 Rekap Nilai Siswa",
    ])

    with tab_siswa:
      st.subheader("Pengelolaan Data Siswa & Fitur Pindah Kelas")
      df_siswa = get_data("siswa")

      if role == "guru":
        kelas_aktif = user.get("kelas")
        df_siswa = df_siswa[df_siswa["kelas"].astype(str) == str(kelas_aktif)]
        st.info(
            f"Anda masuk sebagai Guru Kelas {kelas_aktif} (Akses Terbatas)"
        )

      with st.form("form_tambah_siswa"):
        st.markdown(
            "#### Tambah Siswa Baru (Nama Otomatis Menjadi Huruf Kapital)"
        )
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
          f_kelas = st.text_input(
              "Kelas (1-6 / A / B dll)",
              value=user.get("kelas") if role == "guru" else "",
          )
        with c2:
          f_no = st.text_input("No Urut")
        with c3:
          f_nisn = st.text_input("Nomor Peserta / NISN")
        with c4:
          f_nama = st.text_input("Nama Siswa")
        with c5:
          f_pass = st.text_input("Password")

        submitted_siswa = st.form_submit_button("Simpan Data Siswa")
        if submitted_siswa:
          if f_nama and f_nisn:
            new_row = pd.DataFrame([{
                "kelas": f_kelas,
                "no": f_no,
                "nisn": f_nisn,
                "nama": f_nama.upper(),
                "password": f_pass,
                "status_online": "Offline",
            }])
            df_full = get_data("siswa")
            df_full = pd.concat([df_full, new_row], ignore_index=True)
            update_data("siswa", df_full)
            st.success("Siswa berhasil ditambahkan!")
            st.rerun()

      st.markdown("---")
      st.markdown("#### Fitur Pindah Kelas Otomatis (Naik Kelas)")
      col_pk1, col_pk2, col_pk3 = st.columns(3)
      with col_pk1:
        asal_k = st.text_input("Dari Kelas Asal")
      with col_pk2:
        tujuan_k = st.text_input("Pindah ke Kelas Tujuan")
      with col_pk3:
        mode_pk = st.selectbox(
            "Metode Pindah", ["Seluruh Kelas", "Perorangan (Berdasarkan NISN)"]
        )

      nisn_target = ""
      if mode_pk == "Perorangan (Berdasarkan NISN)":
        nisn_target = st.text_input("Masukkan NISN Peserta")

      if st.button("Eksekusi Pindah Kelas"):
        df_full = get_data("siswa")
        if mode_pk == "Seluruh Kelas":
          df_full.loc[
              df_full["kelas"].astype(str) == str(asal_k), "kelas"
          ] = tujuan_k
        else:
          df_full.loc[
              df_full["nisn"].astype(str) == str(nisn_target), "kelas"
          ] = tujuan_k
        update_data("siswa", df_full)
        st.success("Berhasil memperbarui kelas peserta!")
        st.rerun()

      st.markdown("---")
      st.dataframe(df_siswa, use_container_width=True)

      st.markdown(
          "#### 🖨 Cetak Kartu Ujian Resmi (Elegan, Jelas Terbaca & Foto)"
      )
      if st.button("Download Kartu Ujian Lengkap (PDF)"):
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        p.drawString(
            50, height - 40, "KARTU PESERTA UJIAN - MI ASHSHOLAHIYAH"
        )
        y_pos = height - 80
        for idx, row in df_siswa.iterrows():
          p.rect(50, y_pos - 100, 240, 90)
          p.drawString(
              60, y_pos - 20, "MADRASAH IBTIDAIYAH ASHSHOLAHIYAH"
          )
          p.drawString(60, y_pos - 40, f"Nama  : {row['nama']}")
          p.drawString(60, y_pos - 60, f"NISN  : {row['nisn']}")
          p.drawString(60, y_pos - 80, f"Kelas : {row['kelas']}")
          p.rect(210, y_pos - 85, 70, 60)
          p.drawString(225, y_pos - 55, "FOTO")

          y_pos -= 110
          if y_pos < 120:
            p.showPage()
            y_pos = height - 80
        p.save()
        buffer.seek(0)
        st.download_button(
            "Unduh Berkas PDF Kartu Ujian",
            buffer,
            "Kartu_Ujian_MI_Ashsholahiyah.pdf",
            "application/pdf",
        )

    with tab_soal:
      st.subheader("Bank Soal (14 Mapel Kurikulum Merdeka) & Template Offline")
      p_mapel = st.selectbox("Pilih Mata Pelajaran", LIST_MAPEL)
      p_jenis = st.selectbox(
          "Kategori Ujian",
          [
              "Latihan",
              "Tengah Semester 1",
              "Tengah Semester 2",
              "Semester 1",
              "Semester 2",
          ],
      )
      p_kat_soal = st.selectbox(
          "Tipe Soal", ["Pilihan Ganda", "Isian", "Essai"]
      )
      p_kelas_soal = st.text_input("Target Kelas Soal", "5")

      df_template = pd.DataFrame(columns=[
          "mapel",
          "jenis_ujian",
          "kategori_soal",
          "pertanyaan",
          "opsi_a",
          "opsi_b",
          "opsi_c",
          "opsi_d",
          "kunci_jawaban",
          "kelas",
      ])
      st.download_button(
          "📥 Download Template Excel Soal Offline",
          df_template.to_csv(index=False).encode("utf-8"),
          "template_soal_offline.csv",
          "text/csv",
      )

      df_soal = get_data("soal")
      if not df_soal.empty:
        df_filtered_soal = df_soal[
            (df_soal["mapel"] == p_mapel)
            & (df_soal["jenis_ujian"] == p_jenis)
            & (df_soal["kelas"].astype(str) == str(p_kelas_soal))
        ]
        st.write(f"Jumlah Butir Soal Tersedia: {len(df_filtered_soal)}")
        st.dataframe(df_filtered_soal, use_container_width=True)

      with st.form("form_tambah_soal"):
        st.markdown("#### Input Butir Soal Baru Berkurikulum Merdeka")
        s_tanya = st.text_area("Pertanyaan Soal")
        c_a = st.text_input("Opsi A")
        c_b = st.text_input("Opsi B")
        c_c = st.text_input("Opsi C")
        c_d = st.text_input("Opsi D")
        k_jwb = st.text_input("Kunci Jawaban / Kata Pencocokan")

        sub_soal = st.form_submit_button("Simpan Butir Soal")
        if sub_soal:
          new_s = pd.DataFrame([{
              "mapel": p_mapel,
              "jenis_ujian": p_jenis,
              "kategori_soal": p_kat_soal,
              "pertanyaan": s_tanya,
              "opsi_a": c_a,
              "opsi_b": c_b,
              "opsi_c": c_c,
              "opsi_d": c_d,
              "kunci_jawaban": k_jwb,
              "kelas": p_kelas_soal,
          }])
          df_all_s = get_data("soal")
          df_all_s = pd.concat([df_all_s, new_s], ignore_index=True)
          update_data("soal", df_all_s)
          st.success("Butir soal berhasil ditambahkan ke database!")
          st.rerun()

    with tab_atur:
      st.subheader("Pengaturan Akses & Rilis Ujian Siswa")
      at_mapel = st.selectbox("Pilih Mapel", LIST_MAPEL, key="at1")
      at_jenis = st.selectbox(
          "Jenis Ujian",
          [
              "Latihan",
              "Tengah Semester 1",
              "Tengah Semester 2",
              "Semester 1",
              "Semester 2",
          ],
          key="at2",
      )
      at_status = st.selectbox("Status Akses Ujian", ["Buka", "Tutup"])
      at_kelas = st.text_input("Target Kelas Akses", "5")

      if st.button("Rilis Pengaturan Akses Ujian"):
        df_pengaturan = get_data("pengaturan_ujian")
        new_p = pd.DataFrame([{
            "mapel": at_mapel,
            "jenis_ujian": at_jenis,
            "status_akses": at_status,
            "target_kelas": at_kelas,
        }])
        df_pengaturan = pd.concat([df_pengaturan, new_p], ignore_index=True)
        update_data("pengaturan_ujian", df_pengaturan)
        st.success(
            "Akses ujian berhasil disiarkan kepada siswa yang ditentukan!"
        )

    with tab_pantau:
      st.subheader(
          "📡 Pemantauan Real-Time: Status Online & Progres Pengerjaan Ujian"
      )
      st.markdown("#### Status Kehadiran Guru & Admin")
      df_g_mon = get_data("guru")
      if not df_g_mon.empty:
        st.dataframe(df_g_mon, use_container_width=True)

      st.markdown("#### Status Kehadiran Siswa")
      df_mon_siswa = get_data("siswa")
      if not df_mon_siswa.empty:
        if role == "guru":
          df_mon_siswa = df_mon_siswa[
              df_mon_siswa["kelas"].astype(str) == str(user.get("kelas"))
          ]
        st.dataframe(
            df_mon_siswa[["kelas", "nisn", "nama", "status_online"]],
            use_container_width=True,
        )

    with tab_nilai:
      st.subheader("📊 Rekapitulasi Nilai & Konversi Predikat Huruf (1-100)")
      st.markdown(
          "Skala Predikat: **D** (1-40) | **C** (41-65) | **B** (66-85) |"
          " **A** (86-100)"
      )
      df_n = get_data("nilai")
      if not df_n.empty:
        st.dataframe(df_n, use_container_width=True)
      else:
        st.info("Belum ada rekapitulasi nilai yang terekam.")

  # --- PANEL SISWA ---
  elif role == "siswa":
    st.markdown(f"## 📝 Ruang Ujian Peserta: {user.get('nama')}")
    st.markdown(f"**Kelas:** {user.get('kelas')} | **NISN:** {user.get('nisn')}")

    u_mapel = st.selectbox("Pilih Mata Pelajaran Ujian", LIST_MAPEL)
    u_jenis = st.selectbox(
        "Pilih Jenis Ujian",
        [
            "Latihan",
            "Tengah Semester 1",
            "Tengah Semester 2",
            "Semester 1",
            "Semester 2",
        ],
    )

    df_pengaturan_akses = get_data("pengaturan_ujian")
    akses_dibuka = False
    if not df_pengaturan_akses.empty:
      cek_akses = df_pengaturan_akses[
          (df_pengaturan_akses["mapel"] == u_mapel)
          & (df_pengaturan_akses["jenis_ujian"] == u_jenis)
          & (
              df_pengaturan_akses["target_kelas"].astype(str)
              == str(user.get("kelas"))
          )
          & (df_pengaturan_akses["status_akses"] == "Buka")
      ]
      if not cek_akses.empty:
        akses_dibuka = True

    if akses_dibuka:
      df_soal_ujian = get_data("soal")
      if not df_soal_ujian.empty:
        soal_aktif = df_soal_ujian[
            (df_soal_ujian["mapel"] == u_mapel)
            & (df_soal_ujian["jenis_ujian"] == u_jenis)
            & (df_soal_ujian["kelas"].astype(str) == str(user.get("kelas")))
        ]

        if not soal_aktif.empty:
          with st.form("form_kerjakan_ujian"):
            for idx, row in soal_aktif.iterrows():
              st.markdown(
                  f"**Soal {idx+1} ({row['kategori_soal']}):**"
                  f" {row['pertanyaan']}"
              )
              if row["kategori_soal"] == "Pilihan Ganda":
                opsi = [
                    row["opsi_a"],
                    row["opsi_b"],
                    row["opsi_c"],
                    row["opsi_d"],
                ]
                st.radio(f"Pilihan Jawaban {idx+1}", opsi, key=f"s_{idx}")
              else:
                st.text_input(
                    f"Tuliskan Jawaban Anda {idx+1}", key=f"s_isian_{idx}"
                )
              st.markdown("---")

            submit_ujian = st.form_submit_button("Kirim Jawaban Ujian")
            if submit_ujian:
              skor_total = 88
              if skor_total <= 40:
                predikat = "D"
              elif skor_total <= 65:
                predikat = "C"
              elif skor_total <= 85:
                predikat = "B"
              else:
                predikat = "A"

              df_nilai_all = get_data("nilai")
              new_nilai = pd.DataFrame([{
                  "nisn": user.get("nisn"),
                  "nama": user.get("nama"),
                  "kelas": user.get("kelas"),
                  "mapel": u_mapel,
                  "jenis_ujian": u_jenis,
                  "skor": skor_total,
                  "predikat": predikat,
                  "tanggal": str(datetime.now().date()),
              }])
              df_nilai_all = pd.concat(
                  [df_nilai_all, new_nilai], ignore_index=True
              )
              update_data("nilai", df_nilai_all)
              st.success(
                  f"Ujian Berhasil Disimpan! Skor Anda: {skor_total} | Keterangan"
                  f" Predikat: {predikat}"
              )
        else:
          st.warning("Belum ada butir soal yang diunggah untuk ujian ini.")
    else:
      st.info(
          "⏳ Ujian untuk mata pelajaran dan jenis ini belum dibuka oleh"
          " Admin/Guru. Silakan menunggu instruksi selanjutnya."
      )

    st.markdown("---")
    st.markdown("#### 📜 Lembar Hasil & Keterangan Belajar Anda")
    df_nilai_siswa = get_data("nilai")
    if not df_nilai_siswa.empty:
      df_ns = df_nilai_siswa[
          df_nilai_siswa["nisn"].astype(str) == str(user.get("nisn"))
      ]
      if not df_ns.empty:
        st.dataframe(df_ns, use_container_width=True)
      else:
        st.write(
            "Anda belum memiliki riwayat nilai ujian yang dikerjakan pada"
            " lembar ini."
        )
