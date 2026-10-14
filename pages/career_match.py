
import os
import sys
import tempfile
import math
from datetime import datetime

import pandas as pd
import streamlit as st

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE_DIR, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from auth import get_client
from resume_parser import extract_text_from_pdf
from skill_extractor import extract_key_phrases
import ml_model


def clean_for_json(value):
    """Mengubah nilai pandas/numpy menjadi tipe yang bisa disimpan sebagai JSON."""
    if value is None:
        return None

    if isinstance(value, dict):
        return {
            str(key): clean_for_json(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [clean_for_json(item) for item in value]

    if hasattr(value, "item"):
        try:
            value = value.item()
        except (ValueError, TypeError):
            pass

    if value is None:
        return None

    if isinstance(value, float) and math.isnan(value):
        return None

    if isinstance(value, (str, int, float, bool)):
        return value

    return str(value)


def format_datetime(value):
    if not value:
        return "-"

    try:
        date_value = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )
        return date_value.strftime("%d %B %Y, %H:%M")
    except (ValueError, TypeError):
        return str(value)


def display_skills(skills, empty_message):
    if isinstance(skills, list):
        skills = [str(skill) for skill in skills if skill]

    elif isinstance(skills, str):
        skills = [
            skill.strip()
            for skill in skills.split(",")
            if skill.strip()
        ]

    else:
        skills = []

    return ", ".join(skills[:15]) if skills else empty_message


def display_job_detail(row):
    """Menampilkan detail satu lowongan."""
    title = row.get("job_title") or "Lowongan"
    company = row.get("company") or "Perusahaan"

    try:
        score = float(row.get("match_score") or 0)
    except (ValueError, TypeError):
        score = 0.0

    st.markdown(f"**{title} — {company}**")
    st.progress(max(0.0, min(score, 100.0)) / 100.0)
    st.caption(f"Skor kecocokan: {score:.2f}%")

    role_family = row.get("role_family")
    if role_family:
        st.write(f"**Kategori peran:** {role_family}")

    for column, label in [
        ("location", "Lokasi"),
        ("salary", "Gaji"),
        ("job_type", "Tipe pekerjaan"),
        ("education", "Pendidikan"),
        ("experience", "Pengalaman"),
    ]:
        value = row.get(column)

        if value is not None and str(value).strip():
            st.write(f"**{label}:** {value}")

    description = row.get("description")
    if description:
        st.markdown("**Deskripsi pekerjaan**")
        st.write(description)

    requirements = row.get("requirements")
    if requirements:
        st.markdown("**Kualifikasi / Requirements**")
        st.write(requirements)

    job_link = row.get("job_links")
    if job_link and str(job_link).strip():
        st.markdown(f"[Lihat lowongan]({job_link})")

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**✅ Skill yang Cocok**")
        st.write(
            display_skills(
                row.get("matched_skills"),
                "Belum ada skill yang cocok.",
            )
        )

    with col_b:
        st.markdown("**⚠️ Skill yang Belum Terlihat**")
        st.write(
            display_skills(
                row.get("missing_skills"),
                "Tidak ada gap yang terdeteksi.",
            )
        )


def display_history_item(item, index):
    """Kartu ringkas untuk riwayat Career Match."""
    filename = item.get("cv_filename") or "CV tanpa nama"
    created_at = format_datetime(item.get("created_at"))
    recommendations = item.get("recommendations") or []

    try:
        total = int(item.get("total_recommendations") or 0)
    except (ValueError, TypeError):
        total = 0

    first_score = 0.0
    if recommendations:
        try:
            first_score = float(
                recommendations[0].get("match_score") or 0
            )
        except (ValueError, TypeError, AttributeError):
            pass

    with st.container(border=True):
        col_info, col_score = st.columns([3, 1])

        with col_info:
            st.markdown(f"**📄 {filename}**")
            st.caption(f"🕒 {created_at}")
            st.caption(f"{total} rekomendasi lowongan")

        with col_score:
            st.metric("Skor Tertinggi", f"{first_score:.2f}%")

        with st.expander("Lihat rekomendasi sebelumnya"):
            if recommendations:
                for i, job in enumerate(recommendations, start=1):
                    with st.container(border=True):
                        display_job_detail(job)
            else:
                st.info("Detail rekomendasi tidak tersedia.")


def run_career_match():
    st.title("🎯 Career Match")
    st.write(
        "Upload CV untuk mendapatkan rekomendasi lowongan "
        "yang paling sesuai dengan keterampilanmu."
    )

    uploaded_cv = st.file_uploader(
        "Upload CV (PDF)",
        type=["pdf"],
        key="career_cv",
    )

    top_n = st.slider(
        "Jumlah rekomendasi",
        min_value=3,
        max_value=15,
        value=5,
        key="top_n",
    )

    # =========================================================
    # CARI LOWONGAN DAN SIMPAN OTOMATIS
    # =========================================================
    if st.button("🎯 Cari Lowongan Cocok", type="primary"):
        if uploaded_cv is None:
            st.warning("Mohon upload CV terlebih dahulu.")

        elif not ml_model.is_catalog_available():
            st.error(
                "Katalog data/jobs_processed.csv tidak ditemukan. "
                "Pastikan file tersedia di folder data/."
            )

        else:
            temp_path = None

            # Hapus hasil sebelumnya agar tidak tertukar
            st.session_state.pop("career_match_result", None)

            try:
                with st.spinner("Mencari lowongan paling cocok..."):
                    with tempfile.NamedTemporaryFile(
                        delete=False,
                        suffix=".pdf",
                    ) as tmp_file:
                        tmp_file.write(uploaded_cv.getvalue())
                        temp_path = tmp_file.name

                    cv_text = extract_text_from_pdf(temp_path)

                    if not cv_text.strip():
                        st.error(
                            "Teks tidak dapat diekstrak. Pastikan PDF "
                            "bukan hasil scan gambar."
                        )

                    else:
                        cv_skills = extract_key_phrases(cv_text)

                        recommendations = ml_model.recommend_jobs(
                            cv_text,
                            cv_skills,
                            top_n=top_n,
                        )

                        if recommendations.empty:
                            st.session_state["career_match_result"] = {
                                "cv_filename": uploaded_cv.name,
                                "recommendations": [],
                                "top_n": top_n,
                            }
                            st.info(
                                "Belum ditemukan rekomendasi lowongan."
                            )

                        else:
                            # Ubah DataFrame menjadi daftar dictionary
                            recommendation_list = [
                                clean_for_json(row)
                                for row in recommendations.to_dict(
                                    orient="records"
                                )
                            ]

                            result_data = {
                                "cv_filename": uploaded_cv.name,
                                "recommendations": recommendation_list,
                                "top_n": int(top_n),
                            }

                            # Simpan hasil agar tetap tampil saat rerun
                            st.session_state["career_match_result"] = (
                                result_data
                            )

                            # Simpan otomatis ke riwayat akun pengguna
                            user = st.session_state.get("user", {})
                            user_id = user.get("id")

                            if not user_id:
                                st.warning(
                                    "Rekomendasi berhasil dibuat, "
                                    "tetapi sesi login tidak ditemukan. "
                                    "Riwayat belum tersimpan."
                                )
                            else:
                                try:
                                    client = get_client()

                                    client.table(
                                        "career_match_history"
                                    ).insert({
                                        "user_id": user_id,
                                        "cv_filename": uploaded_cv.name,
                                        "top_n": int(top_n),
                                        "total_recommendations": len(
                                            recommendation_list
                                        ),
                                        "recommendations": (
                                            recommendation_list
                                        ),
                                    }).execute()

                                except Exception:
                                    st.warning(
                                        "Rekomendasi berhasil dibuat, "
                                        "tetapi riwayat belum berhasil "
                                        "ditambahkan."
                                    )

            except Exception as e:
                st.error(f"Gagal mencari rekomendasi: {e}")

            finally:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)

    # =========================================================
    # HASIL REKOMENDASI TERBARU
    # =========================================================
    result_data = st.session_state.get("career_match_result")

    if result_data:
        st.divider()

        recommendations = result_data.get("recommendations", [])
        result_top_n = result_data.get("top_n", top_n)

        st.subheader(
            f"🏆 Top {result_top_n} Lowongan Paling Cocok"
        )

        if recommendations:
            for index, row in enumerate(recommendations, start=1):
                title = row.get("job_title") or "Lowongan"
                company = row.get("company") or "Perusahaan"

                try:
                    score = float(row.get("match_score") or 0)
                except (ValueError, TypeError):
                    score = 0.0

                with st.expander(
                    f"{index}. {title} — {company} | {score:.2f}%",
                    expanded=(index == 1),
                ):
                    display_job_detail(row)

            st.info(
                "Rekomendasi dibuat otomatis berdasarkan data lowongan "
                "yang tersedia dan menjadi referensi awal."
            )
        else:
            st.info("Belum ditemukan rekomendasi lowongan.")

    # =========================================================
    # RIWAYAT CAREER MATCH
    # =========================================================
    st.divider()
    st.subheader("🗂️ Riwayat Career Match")
    st.caption(
        "Lihat kembali hasil rekomendasi dari analisis CV sebelumnya."
    )

    user = st.session_state.get("user", {})
    user_id = user.get("id")

    if not user_id:
        st.info("Login terlebih dahulu untuk melihat riwayat.")
    else:
        try:
            client = get_client()

            response = (
                client.table("career_match_history")
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(10)
                .execute()
            )

            history = response.data or []

            if history:
                for index, item in enumerate(history):
                    display_history_item(item, index)
            else:
                st.info(
                    "Belum ada riwayat Career Match. "
                    "Hasil pencarian berikutnya akan muncul di sini."
                )

        except Exception:
            st.warning(
                "Riwayat belum dapat ditampilkan. "
                "Coba muat ulang halaman beberapa saat lagi."
            )
