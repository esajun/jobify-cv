
import os
import sys
import tempfile
from datetime import datetime

import streamlit as st
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE_DIR, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from auth import get_client
from resume_parser import extract_text_from_pdf
from skill_extractor import (
    extract_key_phrases,
    skill_vocab_size,
    using_trained_vocab,
)
from final_matcher import generate_explanation
import ml_model


def format_datetime(value):
    """Mengubah tanggal riwayat menjadi format yang mudah dibaca."""
    if not value:
        return "-"

    try:
        date_value = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )
        return date_value.strftime("%d %B %Y, %H:%M")
    except (ValueError, TypeError):
        return str(value)


def display_history_item(item, index):
    """Menampilkan satu riwayat analisis dalam bentuk kartu."""
    filename = item.get("cv_filename") or "CV tanpa nama"
    score = float(item.get("final_score") or 0)
    created_at = format_datetime(item.get("created_at"))

    with st.container(border=True):
        col_info, col_score = st.columns([3, 1])

        with col_info:
            st.markdown(f"**{filename}**")
            st.caption(f"🕒 {created_at}")

        with col_score:
            st.metric("Match Score", f"{score:.2f}%")

        job_description = item.get("job_description") or ""

        if job_description:
            st.caption("Deskripsi pekerjaan")
            st.write(
                job_description[:180]
                + ("..." if len(job_description) > 180 else "")
            )

        with st.expander("Lihat detail analisis"):
            c1, c2, c3 = st.columns(3)

            c1.metric(
                "Skill Overlap",
                f"{float(item.get('skill_overlap_ratio') or 0):.2f}%",
            )
            c2.metric(
                "Semantic Similarity",
                f"{float(item.get('semantic_similarity') or 0):.2f}%",
            )
            c3.metric("Match Score", f"{score:.2f}%")

            st.markdown("**🧠 Insight**")
            st.write(item.get("explanation") or "-")

            matched = item.get("matched_skills") or []
            missing = item.get("missing_skills") or []

            col_a, col_b = st.columns(2)

            with col_a:
                st.markdown("**✅ Skill yang Cocok**")
                st.write(
                    ", ".join(matched[:15])
                    if matched
                    else "Belum ada skill yang cocok secara eksplisit."
                )

            with col_b:
                st.markdown("**⚠️ Skill yang Belum Terlihat**")
                st.write(
                    ", ".join(missing[:15])
                    if missing
                    else "Tidak ada gap requirement yang signifikan."
                )


def run_cv_screening():
    st.title("🔍 CV Screening")
    st.write(
        "Upload CV dan masukkan deskripsi pekerjaan untuk "
        "menilai kecocokan kandidat dengan posisi yang dilamar."
    )

    if using_trained_vocab() and ml_model.is_model_available():
        st.caption(
            f"Model ML aktif — {skill_vocab_size()} skill dikenali."
        )
    else:
        st.caption(
            "Model ML belum ditemukan. Sistem menggunakan fallback."
        )

    col_left, col_right = st.columns(2)

    with col_left:
        uploaded_file = st.file_uploader(
            "Upload CV (PDF)",
            type=["pdf"],
            key="screening_cv",
        )

    with col_right:
        job_description = st.text_area(
            "Job Description",
            height=250,
            placeholder="Tempel deskripsi pekerjaan di sini...",
            key="screening_jd",
        )

    # Analisis CV sekaligus menyimpan hasil ke riwayat
    if st.button("🔍 Analisis CV", type="primary"):
        if uploaded_file is None or not job_description.strip():
            st.warning(
                "Upload CV dan isi deskripsi pekerjaan terlebih dahulu."
            )
        else:
            temp_path = None

            # Hapus hasil sebelumnya agar tidak tertukar
            st.session_state.pop("cv_screening_result", None)

            try:
                with st.spinner("Menganalisis CV..."):
                    with tempfile.NamedTemporaryFile(
                        delete=False,
                        suffix=".pdf",
                    ) as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        temp_path = tmp_file.name

                    cv_text = extract_text_from_pdf(temp_path)

                    if not cv_text.strip():
                        st.error(
                            "Teks tidak dapat diekstrak. Pastikan PDF "
                            "bukan hasil scan gambar."
                        )
                    else:
                        cv_skills = extract_key_phrases(cv_text)
                        jd_skills = extract_key_phrases(job_description)

                        matched = sorted(set(cv_skills) & set(jd_skills))
                        missing = sorted(set(jd_skills) - set(cv_skills))

                        result = ml_model.predict_match_score(
                            cv_text=cv_text,
                            cv_skills=cv_skills,
                            job_text=job_description,
                            job_skills=jd_skills,
                        )

                        explanation = generate_explanation(
                            matched,
                            missing,
                        )

                        saved_result = {
                            "cv_filename": uploaded_file.name,
                            "job_description": job_description,
                            "skill_overlap_ratio": float(
                                result["skill_overlap_ratio"]
                            ),
                            "semantic_similarity": float(
                                result["semantic_similarity"]
                            ),
                            "final_score": float(result["final_score"]),
                            "matched_skills": matched,
                            "missing_skills": missing,
                            "explanation": explanation,
                        }

                        # Tampilkan hasil analisis terbaru
                        st.session_state["cv_screening_result"] = (
                            saved_result
                        )

                        # Simpan otomatis ke riwayat pengguna
                        user = st.session_state.get("user", {})
                        user_id = user.get("id")

                        if not user_id:
                            st.warning(
                                "Analisis selesai, tetapi sesi login "
                                "tidak ditemukan. Silakan login kembali."
                            )
                        else:
                            try:
                                client = get_client()

                                client.table(
                                    "cv_screening_history"
                                ).insert({
                                    "user_id": user_id,
                                    **saved_result,
                                }).execute()

                            except Exception:
                                st.warning(
                                    "Analisis selesai, tetapi riwayat "
                                    "belum berhasil ditambahkan. "
                                    "Silakan coba analisis kembali nanti."
                                )

            except Exception as e:
                st.error(f"Gagal menganalisis CV: {e}")

            finally:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)

    # =========================================================
    # HASIL ANALISIS TERBARU
    # =========================================================
    saved_result = st.session_state.get("cv_screening_result")

    if saved_result:
        st.divider()
        st.subheader("📊 Hasil Analisis Terbaru")

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Skill Overlap",
            f"{saved_result['skill_overlap_ratio']:.2f}%",
        )
        c2.metric(
            "Semantic Similarity",
            f"{saved_result['semantic_similarity']:.2f}%",
        )
        c3.metric(
            "Match Score",
            f"{saved_result['final_score']:.2f}%",
        )

        final_score = saved_result["final_score"]

        if final_score >= 75:
            st.success(
                "Sangat direkomendasikan — kandidat sangat sesuai."
            )
        elif final_score >= 50:
            st.warning(
                "Layak dipertimbangkan — masih ada beberapa gap."
            )
        else:
            st.error(
                "Kurang sesuai — terdapat gap yang signifikan."
            )

        # Grafik skor
        scores = {
            "Skill Overlap": saved_result["skill_overlap_ratio"],
            "Semantic Similarity": saved_result["semantic_similarity"],
            "Match Score": final_score,
        }

        st.subheader("📈 Breakdown Skor")

        fig, ax = plt.subplots(figsize=(8, 4))

        bars = ax.bar(
            scores.keys(),
            scores.values(),
            color=["#3b82f6", "#22c55e", "#f97316"],
        )

        ax.set_ylim(0, 110)
        ax.set_ylabel("Skor (%)")

        for bar, value in zip(bars, scores.values()):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                value + 2,
                f"{value:.2f}%",
                ha="center",
            )

        st.pyplot(fig)
        plt.close(fig)

        # Insight
        st.subheader("🧠 Insight")
        st.write(saved_result["explanation"])

        col_a, col_b = st.columns(2)

        with col_a:
            st.subheader("✅ Skill yang Cocok")
            matched = saved_result["matched_skills"]

            st.write(
                ", ".join(matched[:15])
                if matched
                else "Belum ada skill yang cocok secara eksplisit."
            )

        with col_b:
            st.subheader("⚠️ Skill yang Belum Terlihat")
            missing = saved_result["missing_skills"]

            st.write(
                ", ".join(missing[:15])
                if missing
                else "Tidak ada gap requirement yang signifikan."
            )

        st.info(
            "Hasil ini merupakan alat bantu pengambilan keputusan, "
            "bukan pengganti penilaian rekruter."
        )

    # =========================================================
    # RIWAYAT ANALISIS
    # =========================================================
    st.divider()
    st.subheader("🗂️ Riwayat CV Screening")
    st.caption("Menampilkan hingga 10 analisis terbaru dari akunmu.")

    user = st.session_state.get("user", {})
    user_id = user.get("id")

    if not user_id:
        st.info("Login terlebih dahulu untuk melihat riwayat analisis.")
    else:
        try:
            client = get_client()

            response = (
                client.table("cv_screening_history")
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
                    "Belum ada riwayat CV Screening. "
                    "Hasil analisis berikutnya akan muncul di sini."
                )

        except Exception:
            st.warning(
                "Riwayat belum dapat ditampilkan. "
                "Coba muat ulang halaman beberapa saat lagi."
            )
