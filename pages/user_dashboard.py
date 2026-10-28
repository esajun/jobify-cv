
import streamlit as st
import pandas as pd

from auth import get_client
from ui import (
    chips,
    company_logo,
    esc,
    html_block,
    page_header,
    section_title,
    stat_cards,
    to_list,
)


PAGE_SIZE = 20


def run_user_dashboard():
    user = st.session_state.get("user", {})
    client = get_client()

    page_header(
        "Cari",
        "Lowongan Kerja",
        f"Halo, {user.get('full_name', 'User')}! Temukan pekerjaan yang "
        "sesuai dengan minat dan kemampuanmu.",
        badge="Dashboard",
    )

    # ==========================================
    # PILIHAN TAMPILAN
    # ==========================================
    show_all_jobs = st.checkbox(
        "Cari dan filter seluruh lowongan",
        value=False,
        help=(
            "Aktifkan untuk mencari lowongan dari seluruh "
            "data yang tersedia."
        ),
        key="show_all_jobs",
    )

    # ==========================================
    # AMBIL DATA DARI SUPABASE
    # ==========================================
    try:
        if show_all_jobs:
            # Muat seluruh lowongan aktif secara bertahap
            all_jobs = []
            start = 0
            batch_size = 500

            while True:
                response = (
                    client.table("jobs")
                    .select("*")
                    .eq("is_active", True)
                    .order("id", desc=True)
                    .range(start, start + batch_size - 1)
                    .execute()
                )

                batch = response.data or []
                all_jobs.extend(batch)

                if len(batch) < batch_size:
                    break

                start += batch_size

            jobs = pd.DataFrame(all_jobs)

        else:
            # Tampilan awal hanya mengambil 20 lowongan terbaru
            response = (
                client.table("jobs")
                .select("*")
                .eq("is_active", True)
                .order("id", desc=True)
                .limit(PAGE_SIZE)
                .execute()
            )

            jobs = pd.DataFrame(response.data or [])

    except Exception as e:
        st.error(f"Gagal mengambil data lowongan: {e}")
        return

    if jobs.empty:
        st.info("Belum ada lowongan aktif yang tersedia.")
        return

    # ==========================================
    # PASTIKAN KOLOM TERSEDIA
    # ==========================================
    required_columns = [
        "id",
        "title",
        "company",
        "location",
        "city",
        "job_type",
        "education",
        "experience",
        "salary",
        "description",
        "requirements",
        "skills",
        "job_url",
    ]

    for col in required_columns:
        if col not in jobs.columns:
            jobs[col] = ""

    # ==========================================
    # FUNGSI BANTU
    # ==========================================
    def clean(value):
        if value is None:
            return ""

        try:
            if pd.isna(value):
                return ""
        except (TypeError, ValueError):
            pass

        return str(value).strip()

    # ==========================================
    # NORMALISASI LOKASI
    # ==========================================
    def normalize_location(row):
        city = clean(row.get("city", ""))

        if city and city.lower() not in [
            "nan",
            "none",
            "not specified",
            "unknown",
        ]:
            return city.title()

        location = clean(row.get("location", ""))

        if not location:
            return "Lokasi Tidak Dicantumkan"

        text = location.lower()

        city_aliases = {
            "Jakarta Selatan": ["jakarta selatan", "jaksel"],
            "Jakarta Pusat": ["jakarta pusat"],
            "Jakarta Timur": ["jakarta timur"],
            "Jakarta Barat": ["jakarta barat"],
            "Jakarta Utara": ["jakarta utara"],
            "Jakarta": ["jakarta"],
            "Surabaya": ["surabaya"],
            "Bandung": ["bandung"],
            "Semarang": ["semarang"],
            "Yogyakarta": ["yogyakarta", "jogja"],
            "Medan": ["medan"],
            "Makassar": ["makassar"],
            "Malang": ["malang"],
            "Bekasi": ["bekasi"],
            "Tangerang": ["tangerang"],
            "Depok": ["depok"],
            "Bogor": ["bogor"],
            "Sidoarjo": ["sidoarjo"],
            "Surakarta": ["surakarta", "solo"],
            "Denpasar": ["denpasar"],
            "Batam": ["batam"],
            "Cikarang": ["cikarang"],
            "Karawang": ["karawang"],
            "Gresik": ["gresik"],
            "Madiun": ["madiun"],
            "Kediri": ["kediri"],
            "Bali": ["bali"],
        }

        # Cek kota yang lebih spesifik terlebih dahulu
        for city_name, aliases in city_aliases.items():
            if any(alias in text for alias in aliases):
                if city_name == "Jakarta":
                    specific_jakarta = [
                        "jakarta selatan",
                        "jakarta pusat",
                        "jakarta timur",
                        "jakarta barat",
                        "jakarta utara",
                    ]

                    if any(alias in text for alias in specific_jakarta):
                        continue

                return city_name

        suspicious_terms = [
            "head office",
            "office",
            "tower",
            "ruko",
            "kav",
            "jl.",
            "jalan ",
            "rt.",
            "rw.",
            "lantai",
            "gedung",
            "no.",
        ]

        if (
            any(term in text for term in suspicious_terms)
            or any(char.isdigit() for char in location)
        ):
            return "Lokasi Lainnya"

        return location.title()

    # ==========================================
    # NORMALISASI PENDIDIKAN
    # ==========================================
    def normalize_education(value):
        text = clean(value).lower()

        if not text or text in [
            "not specified",
            "none",
            "nan",
            "unknown",
        ]:
            return "Tidak Dicantumkan"

        if any(x in text for x in [
            "doctoral",
            "doctorate",
            "phd",
            "doktor",
        ]):
            return "S3 / Doktor"

        if any(x in text for x in [
            "master",
            "magister",
            "postgraduate",
        ]):
            return "S2 / Magister"

        if any(x in text for x in [
            "bachelor",
            "sarjana",
            "undergraduate",
        ]):
            return "S1 / Sarjana"

        if "diploma" in text:
            return "Diploma"

        if any(x in text for x in [
            "senior high",
            "high school",
            "sma",
            "smk",
        ]):
            return "SMA / SMK"

        if any(x in text for x in [
            "junior high",
            "smp",
        ]):
            return "SMP"

        if any(x in text for x in [
            "elementary",
            "primary school",
            "sekolah dasar",
        ]):
            return "SD"

        return clean(value).title()

    # ==========================================
    # KATEGORI PEKERJAAN
    # ==========================================
    def get_job_category(value):
        text = clean(value).lower()

        categories = {
            "penuh waktu": "Penuh Waktu",
            "full-time": "Penuh Waktu",
            "paruh waktu": "Paruh Waktu",
            "part-time": "Paruh Waktu",
            "kontrak": "Kontrak",
            "contract": "Kontrak",
            "magang": "Magang",
            "internship": "Magang",
            "freelance": "Freelance",
        }

        for keyword, category in categories.items():
            if text.startswith(keyword):
                return category

        return "Lainnya"

    # ==========================================
    # SISTEM KERJA
    # ==========================================
    def get_work_mode(value):
        text = clean(value).lower()

        if "remote" in text or "work from home" in text:
            return "Remote"

        if "hybrid" in text:
            return "Hybrid"

        if any(x in text for x in [
            "di lokasi",
            "on-site",
            "onsite",
            "on site",
        ]):
            return "Di Lokasi"

        return "Tidak Dicantumkan"

    # ==========================================
    # OLAH DATA
    # ==========================================
    jobs["location_display"] = jobs.apply(
        normalize_location,
        axis=1,
    )

    jobs["education_display"] = jobs["education"].apply(
        normalize_education
    )

    jobs["job_category"] = jobs["job_type"].apply(
        get_job_category
    )

    jobs["work_mode"] = jobs["job_type"].apply(
        get_work_mode
    )

    # ==========================================
    # RINGKASAN (kartu statistik ditampilkan setelah filter)
    # ==========================================
    section_title("Temukan Pekerjaanmu")

    with st.container(border=True, key="card_filters"):
        # ==========================================
        # PENCARIAN
        # ==========================================
        keyword = st.text_input(
            "Cari Posisi atau Perusahaan",
            placeholder=(
                "Contoh: Data Analyst, Programmer, "
                "atau nama perusahaan"
            ),
            key="job_keyword",
        )

        # ==========================================
        # FILTER UTAMA
        # ==========================================
        col1, col2, col3 = st.columns(3)

        with col1:
            locations = sorted(
                x
                for x in jobs["location_display"].unique()
                if x and x != "Lokasi Tidak Dicantumkan"
            )

            selected_location = st.selectbox(
                "Lokasi",
                ["Semua Lokasi"] + locations,
            )

        with col2:
            job_types = [
                "Penuh Waktu",
                "Paruh Waktu",
                "Kontrak",
                "Magang",
                "Freelance",
                "Lainnya",
            ]

            selected_type = st.selectbox(
                "Jenis Pekerjaan",
                ["Semua Jenis"] + job_types,
            )

        with col3:
            work_modes = [
                "Di Lokasi",
                "Hybrid",
                "Remote",
                "Tidak Dicantumkan",
            ]

            selected_mode = st.selectbox(
                "Sistem Kerja",
                ["Semua Sistem Kerja"] + work_modes,
            )

        # ==========================================
        # FILTER TAMBAHAN
        # ==========================================
        col4, col5 = st.columns(2)

        with col4:
            education_order = [
                "SD",
                "SMP",
                "SMA / SMK",
                "Diploma",
                "S1 / Sarjana",
                "S2 / Magister",
                "S3 / Doktor",
                "Tidak Dicantumkan",
            ]

            available_educations = set(
                jobs["education_display"].unique()
            )

            educations = [
                item
                for item in education_order
                if item in available_educations
            ]

            other_educations = sorted(
                item
                for item in available_educations
                if item not in education_order and item
            )

            educations.extend(other_educations)

            selected_education = st.selectbox(
                "Pendidikan",
                ["Semua Pendidikan"] + educations,
            )

        with col5:
            experiences = sorted({
                clean(value)
                for value in jobs["experience"]
                if clean(value)
            })

            selected_experience = st.selectbox(
                "Pengalaman",
                ["Semua Pengalaman"] + experiences,
            )

    # ==========================================
    # TERAPKAN FILTER
    # ==========================================
    filtered = jobs.copy()

    if keyword.strip():
        searchable = (
            filtered["title"].fillna("").astype(str)
            + " "
            + filtered["company"].fillna("").astype(str)
            + " "
            + filtered["skills"].fillna("").astype(str)
            + " "
            + filtered["description"].fillna("").astype(str)
        )

        filtered = filtered[
            searchable.str.contains(
                keyword.strip(),
                case=False,
                na=False,
                regex=False,
            )
        ]

    if selected_location != "Semua Lokasi":
        filtered = filtered[
            filtered["location_display"] == selected_location
        ]

    if selected_type != "Semua Jenis":
        filtered = filtered[
            filtered["job_category"] == selected_type
        ]

    if selected_mode != "Semua Sistem Kerja":
        filtered = filtered[
            filtered["work_mode"] == selected_mode
        ]

    if selected_education != "Semua Pendidikan":
        filtered = filtered[
            filtered["education_display"] == selected_education
        ]

    if selected_experience != "Semua Pengalaman":
        filtered = filtered[
            filtered["experience"].apply(clean)
            == selected_experience
        ]

    # ==========================================
    # PAGINATION
    # ==========================================
    total_jobs = len(filtered)

    stat_cards([
        (
            "Lowongan Dimuat" if show_all_jobs else "Lowongan Terbaru",
            f"{len(jobs):,}",
            "seluruh lowongan aktif" if show_all_jobs
            else "20 lowongan terbaru",
            "teal",
        ),
        (
            "Sesuai Filter",
            f"{total_jobs:,}",
            "lowongan ditemukan",
            "coral",
        ),
        (
            "Perusahaan",
            f"{filtered['company'].replace('', pd.NA).nunique():,}",
            "pada hasil pencarian",
            "purple",
        ),
    ])

    if not show_all_jobs:
        st.caption(
            "Menampilkan 20 lowongan terbaru. Aktifkan pilihan "
            "pencarian seluruh lowongan untuk melihat lainnya."
        )

    if filtered.empty:
        st.markdown(
            "<div class='jf-empty'><b>Lowongan tidak ditemukan.</b><br>"
            "Coba ubah kata kunci atau filter.</div>",
            unsafe_allow_html=True,
        )
        return

    section_title(f"Hasil Pencarian ({total_jobs:,} Lowongan)")

    total_pages = (total_jobs + PAGE_SIZE - 1) // PAGE_SIZE

    # Reset ke halaman pertama saat filter berubah
    filter_signature = (
        show_all_jobs,
        keyword.strip(),
        selected_location,
        selected_type,
        selected_mode,
        selected_education,
        selected_experience,
    )

    if st.session_state.get("job_filter_signature") != filter_signature:
        st.session_state["job_filter_signature"] = filter_signature
        st.session_state["job_page"] = 1

    current_page = st.session_state.get("job_page", 1)
    current_page = max(1, min(current_page, total_pages))

    start_index = (current_page - 1) * PAGE_SIZE
    end_index = min(start_index + PAGE_SIZE, total_jobs)

    page_jobs = filtered.iloc[start_index:end_index]

    st.caption(
        f"Menampilkan {start_index + 1}–{end_index} "
        f"dari {total_jobs:,} lowongan"
    )

    # ==========================================
    # KARTU LOWONGAN
    # ==========================================
    for _, job in page_jobs.iterrows():
        title = (
            clean(job["title"])
            or "Posisi Tidak Dicantumkan"
        )

        company = (
            clean(job["company"])
            or "Perusahaan Tidak Dicantumkan"
        )

        location = (
            clean(job["location_display"])
            or "Lokasi Tidak Dicantumkan"
        )

        salary = clean(job["salary"])
        skill_list = to_list(job["skills"])

        meta = [
            (f"📍 {location}", "teal"),
            (f"💼 {clean(job['job_category'])}", "coral"),
            (f"🏢 {clean(job['work_mode'])}", "purple"),
            (
                "🎓 " + (
                    clean(job["education_display"])
                    or "Pendidikan Tidak Dicantumkan"
                ),
                "",
            ),
            (
                "🧑‍💻 " + (
                    clean(job["experience"])
                    or "Pengalaman Tidak Dicantumkan"
                ),
                "",
            ),
        ]

        salary_html = (
            f"<div class='jf-job-salary'>{esc(salary)}</div>"
            if salary else ""
        )

        skills_html = (
            chips(skill_list[:6], "amber") if skill_list else ""
        )

        with st.container(border=True, key=f"card_job_{job['id']}"):
            html_block(
                f"""
                <div class="jf-job">
                    {company_logo(company)}
                    <div class="jf-job-main">
                        <div class="jf-job-title">{esc(title)}</div>
                        <div class="jf-job-company">{esc(company)}</div>
                        {chips(meta)}
                        {salary_html}
                        {skills_html}
                    </div>
                </div>
                """
            )

            with st.expander("Lihat Detail Lowongan"):
                description = clean(job["description"])
                requirements = clean(job["requirements"])

                st.markdown("**Deskripsi Pekerjaan**")
                st.write(
                    description or "Belum ada deskripsi."
                )

                st.markdown("**Persyaratan**")
                st.write(
                    requirements or "Belum ada persyaratan."
                )

                st.markdown("**Keterampilan**")

                if skill_list:
                    html_block(chips(skill_list, "amber"))
                else:
                    st.write("Belum dicantumkan.")

                job_url = clean(job["job_url"])

                if job_url.startswith(("https://", "http://")):
                    st.link_button(
                        "Lihat dan Lamar Lowongan",
                        job_url,
                        type="primary",
                        use_container_width=True,
                    )
                else:
                    st.caption(
                        "Link lamaran belum tersedia. "
                        "Hubungi perusahaan untuk informasi "
                        "lebih lanjut."
                    )

    # ==========================================
    # TOMBOL PAGINATION
    # ==========================================
    if total_pages > 1:
        st.write("")

        prev_col, page_col, next_col = st.columns(
            [1, 2, 1]
        )

        with prev_col:
            if st.button(
                "← Sebelumnya",
                disabled=current_page <= 1,
                use_container_width=True,
            ):
                st.session_state["job_page"] = current_page - 1
                st.rerun()

        with page_col:
            st.markdown(
                f"<div class='jf-pager'>"
                f"Halaman <b>{current_page}</b> dari "
                f"<b>{total_pages}</b></div>",
                unsafe_allow_html=True,
            )

        with next_col:
            if st.button(
                "Berikutnya →",
                disabled=current_page >= total_pages,
                use_container_width=True,
            ):
                st.session_state["job_page"] = current_page + 1
                st.rerun()

