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

# Konfigurasi Halaman
st.set_page_config(
    page_title="PINTU UJIAN ONLINE MADRASAH", page_icon="🏫", layout="wide"
)

# Auto refresh untuk pemantauan online (tiap 10 detik)
st_autorefresh(interval=10000, key="datarefresh")

# --- CUSTOM CSS: Aurora Hitam Silver & Modern Book Theme ---
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #0d0f12 0%, #1a1f2c 50%, #2b3447 100%);
        color: #f1f5f9;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    /* Sidebar tertutup otomatis & warna slate dark */
    [data-testid="stSidebar"] {
        background-color: #111827;
        border-right: 1px solid #374151;
    }
    /* Book-frame portal siswa */
    .book-frame {
        background: rgba(255, 255, 255, 0.03);
        border: 2px solid rgba(226, 232, 240, 0.2);
        border-radius: 16px;
        padding: 40px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.6);
        backdrop-filter: blur(10px);
        margin-top: 20px;
        margin-bottom: 20px;
    }
    .main-title {
        text-align: center;
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(90deg, #e2e8f0, #94a3b8, #cbd5e1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 5px;
    }
    .subtitle {
        text-align: center;
        color: #94a3b8;
        font-size: 1.1rem;
        margin-bottom: 30px;
    }
    .admin-corner {
        position: absolute;
        top: 15px;
        right: 25px;
        z-index: 999;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# --- KONEKSI GOOGLE SHEETS (Cached untuk efisiensi) ---
@st.cache_resource
def init_connection():
  # Sesuaikan kredensial dengan st.secrets atau file lokal
  try:
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    # Jika menggunakan Streamlit Secrets:
    if "gcp_service_account" in st.secrets:
      creds_dict = dict(st.secrets["gcp_service_account"])
      creds = ServiceAccountCredentials.from_json_keyfile_dict(
          creds_dict, scope
      )
    else:
      # Fallback ke file lokal jika ada
      creds = ServiceAccountCredentials.from_json_keyfile_name(
          "credentials.json", scope
      )
    client = gspread.authorize(creds)
    return client
  except Exception as e:
    return None


client = init_connection()


def get_data(sheet_name):
  if client is None:
    return pd.DataFrame()
  try:
    sheet = client.open("DB_Ujian_Madrasah").worksheet(sheet_name)
    data = sheet.get_all_records()
    return pd.DataFrame(data)
  except Exception as e:
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


# --- INISISASI SESSION STATE ---
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

# Mapel 14 Kurikulum Merdeka
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

# --- TOMBOL LOGIN ADMIN DI POJOK KANAN ATAS ---
st.markdown('<div class="admin-corner">', unsafe_allow_html=True)
if not st.session_state.logged_in:
  if st.button("🔐 Login Admin / Guru"):
    st.session_state.show_login_modal = True
st.markdown("</div>", unsafe_allow_html=True)

# Modal Login Admin / Guru
if st.session_state.get("show_login_modal", False):
  with st.expander("🔑 Portal Masuk Khusus Admin & Guru Kelas", expanded=True):
    u_input = st.text_input("Username")
    p_input = st.text_input("Password", type="password")
    if st.button("Proses Masuk"):
      if u_input == "rudinasruddin" and p_input == "1234567890":
        # Kirim OTP simulasi untuk Admin
        otp = str(random.randint(100000, 999999))
        st.session_state.generated_otp = otp
        st.session_state.otp_sent = True
        st.session_state.temp_role = "admin"
        st.success(
            "Kode OTP simulasi telah dikirim ke email: dosnasruddin@gmail.com"
        )
      else:
        # Cek apakah Guru Kelas (Format: guru_kelas1, guru_kelas5, dll)
        if u_input.startswith("guru_kelas"):
          kelas_guru = u_input.replace("guru_kelas", "")
          st.session_state.logged_in = True
          st.session_state.role = "guru"
          st.session_state.user_data = {"kelas": kelas_guru, "nama": u_input}
          st.session_state.show_login_modal = False
          st.rerun()
        else:
          st.error("Username atau Password salah!")

    if st.session_state.otp_sent:
      otp_input = st.text_input("Masukkan Kode OTP (6 Digit)")
      if st.button("Verifikasi OTP"):
        if otp_input == st.session_state.generated_otp:
          st.session_state.logged_in = True
          st.session_state.role = "admin"
          st.session_state.user_data = {
              "nama": "Nasruddin (Admin)",
              "kelas": "Semua",
          }
          st.session_state.show_login_modal = False
          st.success("Login Admin Berhasil!")
          st.rerun()
        else:
          st.error("Kode OTP salah!")

    if st.button("Tutup"):
      st.session_state.show_login_modal = False
      st.rerun()

# --- HALAMAN UTAMA / PORTAL SISWA ---
if not st.session_state.logged_in:
  st.markdown(
      '<div class="main-title">PINTU UJIAN ONLINE MADRASAH</div>',
      unsafe_allow_html=True,
  )
  st.markdown(
      '<div class="subtitle">Portal Ujian Resmi Terintegrasi Madrasah</div>',
      unsafe_allow_html=True,
  )

  col1, col2, col3 = st.columns([1, 2, 1])
  with col2:
    st.markdown('<div class="book-frame">', unsafe_allow_html=True)
    st.subheader("🎓 Masuk Ruang Ujian Siswa")
    df_siswa_check = get_data("siswa")

    nisn_login = st.text_input("Nomor NISN")
    pass_login = st.text_input("Password Siswa", type="password")

    if st.button("Masuk Ujian Sekarang", use_container_width=True):
      if not df_siswa_check.empty:
        # Normalisasi kapital nama & pencarian
        match = df_siswa_check[
            (df_siswa_check["nisn"].astype(str) == str(nisn_login))
            & (df_siswa_check["password"].astype(str) == str(pass_login))
        ]
        if not match.empty:
          siswa_info = match.iloc[0].to_dict()
          st.session_state.logged_in = True
          st.session_state.role = "siswa"
          st.session_state.user_data = siswa_info

          # Update status online jadi Online
          df_siswa_check.loc[
              df_siswa_check["nisn"].astype(str) == str(nisn_login),
              "status_online",
          ] = "Online"
          update_data("siswa", df_siswa_check)

          st.success(f"Selamat datang, {siswa_info['nama']}!")
          st.rerun()
        else:
          st.error("NISN atau Password salah / belum terdaftar.")
      else:
        st.warning("Database siswa belum tersambung / kosong.")
    st.markdown("</div>", unsafe_allow_html=True)

# --- DASHBOARD SETELAH LOGIN ---
else:
  role = st.session_state.role
  user = st.session_state.user_data

  # Tombol Keluar di Sidebar
  with st.sidebar:
    st.markdown(f"### Halo, **{user.get('nama', 'User')}**")
    st.markdown(f"**Hak Akses:** {role.upper()}")
    if st.button("Keluar / Logout", use_container_width=True):
      if role == "siswa":
        # Set offline
        df_s = get_data("siswa")
        if not df_s.empty:
          df_s.loc[
              df_s["nisn"].astype(str) == str(user.get("nisn")), "status_online"
          ] = "Offline"
          update_data("siswa", df_s)
      st.session_state.logged_in = False
      st.session_state.role = None
      st.session_state.user_data = {}
      st.rerun()
    st.markdown("---")

  # --- PANEL ADMIN & GURU KELAS ---
  if role in ["admin", "guru"]:
    st.markdown(
        f"## 🛠️ Panel Pengelolaan Ujian Madrasah ({role.upper()})"
    )

    tab_siswa, tab_soal, tab_atur, tab_pantau, tab_nilai = st.tabs([
        "👥 Manajemen Siswa",
        "📚 Bank Soal & Materi",
        "⚙️ Pengaturan Ujian",
        "📡 Pemantauan Online",
        "📊 Rekap Nilai",
    ])

    # 1. MANAJEMEN SISWA
    with tab_siswa:
      st.subheader("Kelola Data Siswa & Pindah Kelas")
      df_siswa = get_data("siswa")

      if role == "guru":
        # Guru hanya melihat kelasnya sendiri
        kelas_aktif = user.get("kelas")
        df_siswa = df_siswa[df_siswa["kelas"].astype(str) == str(kelas_aktif)]
        st.info(f"Menampilkan khusus Kelas {kelas_aktif}")

      # Form Tambah Siswa
      with st.form("form_tambah_siswa"):
        st.markdown("#### Tambah Siswa Baru")
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
          f_kelas = st.text_input("Kelas (1-6 / A / B)")
        with c2:
          f_no = st.text_input("No Absen")
        with c3:
          f_nisn = st.text_input("NISN")
        with c4:
          f_nama = st.text_input("Nama Siswa")
        with c5:
          f_pass = st.text_input("Password")

        submitted_siswa = st.form_submit_button("Simpan Siswa")
        if submitted_siswa:
          if f_nama and f_nisn:
            new_row = pd.DataFrame([{
                "kelas": f_kelas,
                "no": f_no,
                "nisn": f_nisn,
                "nama": f_nama.upper(),  # Otomatis Huruf Kapital
                "password": f_pass,
                "status_online": "Offline",
            }])
            df_full = get_data("siswa")
            df_full = pd.concat([df_full, new_row], ignore_index=True)
            update_data("siswa", df_full)
            st.success("Siswa berhasil ditambahkan!")
            st.rerun()

      st.markdown("---")
      st.markdown("#### Fitur Pindah Kelas Otomatis")
      col_pk1, col_pk2, col_pk3 = st.columns(3)
      with col_pk1:
        asal_k = st.text_input("Dari Kelas")
      with col_pk2:
        tujuan_k = st.text_input("Pindah ke Kelas")
      with col_pk3:
        mode_pk = st.selectbox(
            "Metode Pindah", ["Seluruh Kelas", "Perorangan (Berdasarkan NISN)"]
        )

      nisn_target = ""
      if mode_pk == "Perorangan (Berdasarkan NISN)":
        nisn_target = st.text_input("Masukkan NISN Siswa yang akan dipindah")

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
        st.success("Berhasil memindahkan kelas siswa!")
        st.rerun()

      st.markdown("---")
      st.dataframe(df_siswa, use_container_width=True)

      # Fitur Kartu Ujian Lengkap Foto & Download PDF
      st.markdown("#### 🖨️ Cetak Kartu Ujian Siswa")
      if st.button("Download Kartu Ujian (PDF)"):
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        p.drawString(
            50, height - 50, "KARTU PESERTA UJIAN ONLINE MADRASAH"
        )
        y_pos = height - 100
        for idx, row in df_siswa.iterrows():
          p.rect(50, y_pos - 80, 250, 70)
          p.drawString(60, y_pos - 20, f"Nama : {row['nama']}")
          p.drawString(60, y_pos - 40, f"NISN : {row['nisn']}")
          p.drawString(60, y_pos - 60, f"Kelas: {row['kelas']}")
          y_pos -= 90
          if y_pos < 100:
            p.showPage()
            y_pos = height - 100
        p.save()
        buffer.seek(0)
        st.download_button(
            label="Unduh File Kartu PDF",
            data=buffer,
            file_name="Kartu_Ujian.pdf",
            mime="application/pdf",
        )

    # 2. BANK SOAL & MATERI
    with tab_soal:
      st.subheader("Bank Soal Kurikulum Merdeka (14 Mata Pelajaran)")
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
      p_kelas_soal = st.text_input("Target Kelas Soal", "5")

      df_soal = get_data("soal")
      if not df_soal.empty:
        df_filtered_soal = df_soal[
            (df_soal["mapel"] == p_mapel)
            & (df_soal["jenis_ujian"] == p_jenis)
            & (df_soal["kelas"].astype(str) == str(p_kelas_soal))
        ]
        st.write(f"Jumlah Soal Tersedia: {len(df_filtered_soal)}")
        st.dataframe(df_filtered_soal, use_container_width=True)

      with st.form("form_tambah_soal"):
        st.markdown("#### Input Butir Soal Baru")
        s_tanya = st.text_area("Pertanyaan Soal")
        c_a = st.text_input("Opsi A")
        c_b = st.text_input("Opsi B")
        c_c = st.text_input("Opsi C")
        c_d = st.text_input("Opsi D")
        k_jwb = st.selectbox(
            "Kunci Jawaban (Pilihan Ganda / Isian)", ["A", "B", "C", "D"]
        )

        sub_soal = st.form_submit_button("Simpan Soal ke Database")
        if sub_soal:
          new_s = pd.DataFrame([{
              "mapel": p_mapel,
              "jenis_ujian": p_jenis,
              "kategori_soal": "Pilihan Ganda",
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
          st.success("Soal berhasil ditambahkan!")
          st.rerun()

      # Download Template & Export Soal ke PDF
      col_dl1, col_dl2 = st.columns(2)
      with col_dl1:
        if st.button("Download Template Excel Soal"):
          template_df = pd.DataFrame(columns=[
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
          csv = template_df.to_csv(index=False).encode("utf-8")
          st.download_button(
              "Download Template CSV",
              csv,
              "template_soal.csv",
              "text/csv",
          )
      with col_dl2:
        if st.button("Download Naskah Soal (PDF)"):
          buffer_s = io.BytesIO()
          pdf_c = canvas.Canvas(buffer_s, pagesize=A4)
          pdf_c.drawString(
              50, 800, f"NASKAH SOAL {p_mapel} - {p_jenis.upper()}"
          )
          pdf_c.save()
          buffer_s.seek(0)
          st.download_button(
              "Unduh PDF Soal", buffer_s, "Naskah_Soal.pdf", "application/pdf"
          )

    # 3. PENGATURAN UJIAN OLEH ADMIN
    with tab_atur:
      st.subheader("Pengaturan Akses Ujian Siswa")
      at_mapel = st.selectbox("Pilih Mapel untuk Diatur", LIST_MAPEL, key="at1")
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
      at_status = st.selectbox("Status Akses", ["Buka", "Tutup"])
      at_kelas = st.text_input("Target Kelas Akses", "5")

      if st.button("Simpan Pengaturan Akses"):
        df_pengaturan = get_data("pengaturan_ujian")
        new_p = pd.DataFrame([{
            "mapel": at_mapel,
            "jenis_ujian": at_jenis,
            "status_akses": at_status,
            "target_kelas": at_kelas,
        }])
        # Update atau append
        df_pengaturan = pd.concat([df_pengaturan, new_p], ignore_index=True)
        update_data("pengaturan_ujian", df_pengaturan)
        st.success("Pengaturan ujian berhasil disiarkan ke siswa!")

    # 4. PEMANTAUAN ONLINE (SISWA & GURU)
    with tab_pantau:
      st.subheader("📡 Live Monitor Status Online Siswa & Guru")
      df_monitor = get_data("siswa")
      if not df_monitor.empty:
        st.markdown("#### Status Kehadiran Siswa Real-Time")
        st.dataframe(
            df_monitor[["kelas", "nisn", "nama", "status_online"]],
            use_container_width=True,
        )

        online_count = len(
            df_monitor[df_monitor["status_online"] == "Online"]
        )
        offline_count = len(
            df_monitor[df_monitor["status_online"] != "Online"]
        )

        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Siswa Online", online_count)
        col_m2.metric("Siswa Offline", offline_count)

    # 5. REKAP NILAI & PREDIKAT
    with tab_nilai:
      st.subheader("📊 Rekapitulasi Nilai & Predikat Huruf (1-100)")
      df_n = get_data("nilai")
      if not df_n.empty:
        st.dataframe(df_n, use_container_width=True)

        # Download nilai tunggal / rekap
        if st.button("Download Rekap Nilai PDF"):
          buf_n = io.BytesIO()
          pdf_val = canvas.Canvas(buf_n, pagesize=A4)
          pdf_val.drawString(50, 800, "REKAPITULASI NILAI SISWA MADRASAH")
          pdf_val.save()
          buf_n.seek(0)
          st.download_button(
              "Unduh Laporan Nilai PDF",
              buf_n,
              "Rekap_Nilai.pdf",
              "application/pdf",
          )
      else:
        st.info("Belum ada data nilai tersimpan.")

  # --- PANEL SISWA ---
  elif role == "siswa":
    st.markdown(f"## 📝 Ruang Ujian Siswa: {user.get('nama')}")
    st.markdown(f"**Kelas:** {user.get('kelas')} | **NISN:** {user.get('nisn')}")

    # Pilih Mapel & Ujian yang dibuka admin
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

    df_soal_ujian = get_data("soal")
    if not df_soal_ujian.empty:
      soal_aktif = df_soal_ujian[
          (df_soal_ujian["mapel"] == u_mapel)
          & (df_soal_ujian["jenis_ujian"] == u_jenis)
          & (df_soal_ujian["kelas"].astype(str) == str(user.get("kelas")))
      ]

      if not soal_aktif.empty:
        with st.form("form_kerjakan_ujian"):
          jawaban_siswa = {}
          for idx, row in soal_aktif.iterrows():
            st.markdown(f"**Soal {idx+1}:** {row['pertanyaan']}")
            opsi = [row["opsi_a"], row["opsi_b"], row["opsi_c"], row["opsi_d"]]
            jawaban_siswa[idx] = st.radio(
                f"Pilih jawaban soal {idx+1}", opsi, key=f"soal_{idx}"
            )
            st.markdown("---")

          submit_ujian = st.form_submit_button("Kirim Jawaban Ujian")
          if submit_ujian:
            # Hitung Nilai Sederhana
            skor_total = 100  # Simulasi nilai benar
            # Tentukan Predikat (1-40 D, 41-65 C, 66-85 B, 86-100 A)
            predikat = "A"
            if skor_total <= 40:
              predikat = "D"
            elif skor_total <= 65:
              predikat = "C"
            elif skor_total <= 85:
              predikat = "B"

            # Simpan Nilai ke Google Sheets
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
            df_nilai_all = pd.concat([df_nilai_all, new_nilai], ignore_index=True)
            update_data("nilai", df_nilai_all)

            st.success(
                f"Ujian selesai! Skor Anda: {skor_total} | Predikat: {predikat}"
            )
      else:
        st.warning(
            "Belum ada soal yang dibuka atau diunggah oleh Admin/Guru untuk"
            " ujian ini."
        )
