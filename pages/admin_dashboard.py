import streamlit as st

from ui import page_header, stat_cards


# ==========================================
# HELPER
# ==========================================

def fetch_all_jobs(client, page_size=1000):
    """Mengambil seluruh data lowongan dari Supabase secara bertahap."""
    all_jobs = []
    start = 0

    while True:
        response = (
            client.table("jobs")
            .select("*")
            .order("id", desc=True)
            .range(start, start + page_size - 1)
            .execute()
        )

        batch = response.data or []
        all_jobs.extend(batch)

        if len(batch) < page_size:
            break

        start += page_size

    return all_jobs


def show_flash_message():
    """Menampilkan notifikasi setelah aplikasi melakukan rerun."""
    flash = st.session_state.pop("admin_flash", None)

    if flash:
        message_type, message = flash

        if message_type == "success":
            st.success(message)
        elif message_type == "error":
            st.error(message)


def clear_add_form():
    """Mengosongkan semua input pada form tambah lowongan."""
    fields = [
        "add_title",
        "add_company",
        "add_location",
        "add_salary",
        "add_job_type",
        "add_education",
        "add_experience",
        "add_skills",
        "add_requirements",
        "add_benefits",
        "add_description",
        "add_job_url",
    ]

    for field in fields:
        st.session_state[field] = ""

    st.session_state["add_is_active"] = True


def format_job_label(job_id, jobs):
    """Membuat label pilihan lowongan berdasarkan ID dan judul."""
    job = next(
        (item for item in jobs if item.get("id") == job_id),
        {},
    )

    title = job.get("title") or "Tanpa judul"
    company = job.get("company") or "Perusahaan tidak diketahui"

    return f"ID {job_id} — {title} ({company})"


def make_job_payload(
    title,
    company,
    location,
    salary,
    job_type,
    education,
    experience,
    skills,
    requirements,
    benefits,
    description,
    job_url,
    is_active,
):
    """Merapikan data sebelum dikirim ke Supabase."""
    return {
        "title": title.strip(),
        "company": company.strip() or None,
        "location": location.strip() or None,
        "salary": salary.strip() or None,
        "job_type": job_type.strip() or None,
        "education": education.strip() or None,
        "experience": experience.strip() or None,
        "skills": skills.strip() or None,
        "requirements": requirements.strip() or None,
        "benefits": benefits.strip() or None,
        "description": description.strip() or None,
        "job_url": job_url.strip() or None,
        "is_active": is_active,
    }


# ==========================================
# DASHBOARD ADMIN
# ==========================================

def run_admin_dashboard(client):
    page_header(
        "Dashboard",
        "Admin",
        "Kelola katalog lowongan kerja Jobify.",
        badge="Admin",
    )

    # Tampilkan notifikasi dari aksi sebelumnya
    show_flash_message()

    # ==========================================
    # AMBIL SEMUA DATA LOWONGAN
    # ==========================================

    try:
        with st.spinner("Memuat seluruh data lowongan..."):
            jobs = fetch_all_jobs(client)
    except Exception as e:
        st.error(f"Gagal mengambil data lowongan: {e}")

        if st.button("Coba Muat Ulang", key="retry_load_jobs"):
            st.rerun()

        return

    # ==========================================
    # STATISTIK
    # ==========================================

    total_jobs = len(jobs)

    active_jobs = sum(
        1 for job in jobs
        if job.get("is_active", False)
    )

    inactive_jobs = total_jobs - active_jobs

    stat_cards([
        ("Total Lowongan", f"{total_jobs:,}", "seluruh katalog", "teal"),
        ("Lowongan Aktif", f"{active_jobs:,}", "tampil untuk pengguna", "purple"),
        ("Lowongan Nonaktif", f"{inactive_jobs:,}", "disembunyikan", "coral"),
    ])

    tab_list, tab_add, tab_edit, tab_delete = st.tabs([
        "Daftar Lowongan",
        "Tambah Lowongan",
        "Edit Lowongan",
        "Hapus Lowongan",
    ])

    # ==========================================
    # DAFTAR LOWONGAN
    # ==========================================

    with tab_list:
        header_col, refresh_col = st.columns([5, 1])

        with header_col:
            st.subheader("Daftar Lowongan")
            st.caption(f"Total {total_jobs:,} lowongan ditemukan.")

        with refresh_col:
            if st.button(
                "Refresh",
                key="refresh_job_list",
                use_container_width=True,
            ):
                st.rerun()

        if jobs:
            search = st.text_input(
                "Cari posisi atau perusahaan",
                placeholder="Contoh: Data Analyst, Google...",
                key="admin_job_search",
            )

            status_filter = st.selectbox(
                "Status lowongan",
                ["Semua", "Aktif", "Nonaktif"],
                key="admin_job_status",
            )

            filtered_jobs = jobs

            if search.strip():
                keyword = search.strip().lower()

                filtered_jobs = [
                    job for job in filtered_jobs
                    if keyword in str(
                        job.get("title") or ""
                    ).lower()
                    or keyword in str(
                        job.get("company") or ""
                    ).lower()
                ]

            if status_filter == "Aktif":
                filtered_jobs = [
                    job for job in filtered_jobs
                    if job.get("is_active", False)
                ]

            elif status_filter == "Nonaktif":
                filtered_jobs = [
                    job for job in filtered_jobs
                    if not job.get("is_active", False)
                ]

            st.caption(
                f"Menampilkan {len(filtered_jobs):,} dari "
                f"{total_jobs:,} lowongan."
            )

            if filtered_jobs:
                st.dataframe(
                    [
                        {
                            "ID": job.get("id"),
                            "Posisi": job.get("title"),
                            "Perusahaan": job.get("company"),
                            "Lokasi": job.get("location"),
                            "Gaji": job.get("salary"),
                            "Tipe Pekerjaan": job.get("job_type"),
                            "Aktif": (
                                "Ya" if job.get("is_active", False)
                                else "Tidak"
                            ),
                        }
                        for job in filtered_jobs
                    ],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info(
                    "Tidak ada lowongan yang sesuai dengan filter."
                )

        else:
            st.info("Belum ada lowongan.")

    # ==========================================
    # TAMBAH LOWONGAN
    # ==========================================

    with tab_add:
        st.subheader("Tambah Lowongan")
        st.caption("Isi informasi lowongan yang ingin ditambahkan.")

        with st.form("add_job_form"):
            title = st.text_input(
                "Nama posisi *",
                key="add_title",
            )

            company = st.text_input(
                "Perusahaan",
                key="add_company",
            )

            location = st.text_input(
                "Lokasi",
                key="add_location",
            )

            salary = st.text_input(
                "Gaji",
                key="add_salary",
            )

            job_type = st.text_input(
                "Tipe pekerjaan",
                key="add_job_type",
            )

            education = st.text_input(
                "Pendidikan",
                key="add_education",
            )

            experience = st.text_input(
                "Pengalaman",
                key="add_experience",
            )

            skills = st.text_area(
                "Skill",
                key="add_skills",
            )

            requirements = st.text_area(
                "Persyaratan",
                key="add_requirements",
            )

            benefits = st.text_area(
                "Benefit",
                key="add_benefits",
            )

            description = st.text_area(
                "Deskripsi pekerjaan",
                key="add_description",
            )

            job_url = st.text_input(
                "URL lowongan",
                key="add_job_url",
            )

            is_active = st.checkbox(
                "Lowongan aktif",
                value=True,
                key="add_is_active",
            )

            save_col, clear_col = st.columns(2)

            with save_col:
                submitted = st.form_submit_button(
                    "Simpan Lowongan",
                    type="primary",
                    use_container_width=True,
                )

            with clear_col:
                clear_submitted = st.form_submit_button(
                    "Clear Form",
                    on_click=clear_add_form,
                    use_container_width=True,
                )

        # Proses simpan hanya ketika tombol simpan ditekan
        if submitted:
            if not title.strip():
                st.error("Gagal menambahkan lowongan: nama posisi wajib diisi.")
            else:
                payload = make_job_payload(
                    title,
                    company,
                    location,
                    salary,
                    job_type,
                    education,
                    experience,
                    skills,
                    requirements,
                    benefits,
                    description,
                    job_url,
                    is_active,
                )

                try:
                    client.table("jobs").insert(payload).execute()

                    st.session_state["admin_flash"] = (
                        "success",
                        f"Lowongan '{title.strip()}' berhasil ditambahkan.",
                    )

                    st.rerun()

                except Exception as e:
                    st.error(f"Gagal menambahkan lowongan: {e}")

    # ==========================================
    # EDIT LOWONGAN
    # ==========================================

    with tab_edit:
        st.subheader("Edit Lowongan")

        if not jobs:
            st.info("Belum ada lowongan untuk diedit.")

        else:
            job_ids = [job["id"] for job in jobs]

            selected_id = st.selectbox(
                "Pilih lowongan",
                job_ids,
                format_func=lambda job_id: format_job_label(
                    job_id, jobs
                ),
                key="edit_job_id",
            )

            job = next(
                item for item in jobs
                if item["id"] == selected_id
            )

            with st.form("edit_job_form"):
                title = st.text_input(
                    "Nama posisi *",
                    value=job.get("title") or "",
                )

                company = st.text_input(
                    "Perusahaan",
                    value=job.get("company") or "",
                )

                location = st.text_input(
                    "Lokasi",
                    value=job.get("location") or "",
                )

                salary = st.text_input(
                    "Gaji",
                    value=job.get("salary") or "",
                )

                job_type = st.text_input(
                    "Tipe pekerjaan",
                    value=job.get("job_type") or "",
                )

                education = st.text_input(
                    "Pendidikan",
                    value=job.get("education") or "",
                )

                experience = st.text_input(
                    "Pengalaman",
                    value=job.get("experience") or "",
                )

                skills = st.text_area(
                    "Skill",
                    value=job.get("skills") or "",
                )

                requirements = st.text_area(
                    "Persyaratan",
                    value=job.get("requirements") or "",
                )

                benefits = st.text_area(
                    "Benefit",
                    value=job.get("benefits") or "",
                )

                description = st.text_area(
                    "Deskripsi pekerjaan",
                    value=job.get("description") or "",
                )

                job_url = st.text_input(
                    "URL lowongan",
                    value=job.get("job_url") or "",
                )

                is_active = st.checkbox(
                    "Lowongan aktif",
                    value=job.get("is_active", True),
                )

                submitted = st.form_submit_button(
                    "Simpan Perubahan",
                    type="primary",
                    use_container_width=True,
                )

            if submitted:
                if not title.strip():
                    st.error(
                        "Gagal mengedit lowongan: "
                        "nama posisi wajib diisi."
                    )
                else:
                    payload = make_job_payload(
                        title,
                        company,
                        location,
                        salary,
                        job_type,
                        education,
                        experience,
                        skills,
                        requirements,
                        benefits,
                        description,
                        job_url,
                        is_active,
                    )

                    try:
                        (
                            client.table("jobs")
                            .update(payload)
                            .eq("id", selected_id)
                            .execute()
                        )

                        st.session_state["admin_flash"] = (
                            "success",
                            f"Lowongan '{title.strip()}' berhasil diperbarui.",
                        )

                        st.rerun()

                    except Exception as e:
                        st.error(f"Gagal mengedit lowongan: {e}")

    # ==========================================
    # HAPUS LOWONGAN
    # ==========================================

    with tab_delete:
        st.subheader("Hapus Lowongan")

        if not jobs:
            st.info("Belum ada lowongan untuk dihapus.")

        else:
            delete_id = st.selectbox(
                "Pilih lowongan yang akan dihapus",
                [job["id"] for job in jobs],
                format_func=lambda job_id: format_job_label(
                    job_id, jobs
                ),
                key="delete_job_id",
            )

            selected_job = next(
                item for item in jobs
                if item["id"] == delete_id
            )

            st.warning(
                f"Lowongan: {selected_job.get('title') or '-'}\n\n"
                f"Perusahaan: "
                f"{selected_job.get('company') or 'Tidak diketahui'}"
            )

            confirm = st.checkbox(
                "Saya yakin ingin menghapus lowongan ini.",
                key="confirm_delete_job",
            )

            if st.button(
                "Hapus Permanen",
                type="primary",
                disabled=not confirm,
                key="delete_job_button",
            ):
                try:
                    (
                        client.table("jobs")
                        .delete()
                        .eq("id", delete_id)
                        .execute()
                    )

                    st.session_state["admin_flash"] = (
                        "success",
                        f"Lowongan '{selected_job.get('title') or '-'}' "
                        "berhasil dihapus.",
                    )

                    # Reset konfirmasi agar tidak aktif lagi
                    st.session_state["confirm_delete_job"] = False

                    st.rerun()

                except Exception as e:
                    st.error(f"Gagal menghapus lowongan: {e}")
