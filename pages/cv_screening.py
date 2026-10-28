
import os
import sys
import tempfile
from datetime import datetime

import streamlit as st

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE_DIR, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from auth import get_client
from ui import (
    chips,
    esc,
    html_block,
    meter,
    page_header,
    score_ring,
    section_title,
    text_to_html,
)
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


def skills_html(skills, empty_message, tone):
    items = [str(x) for x in (skills or []) if x][:15]

    if not items:
        return f"<p class='jf-muted-note'>{esc(empty_message)}</p>"

    return chips(items, tone)


def display_history_item(item, index):
    """Menampilkan satu riwayat analisis dalam bentuk kartu."""
    filename = item.get("cv_filename") or "CV tanpa nama"
    score = float(item.get("final_score") or 0)
    created_at = format_datetime(item.get("created_at"))

    job_description = item.get("job_description") or ""
    snippet = job_description[:180] + (
        "..." if len(job_description) > 180 else ""
    )
    snippet_html = (
        f"<div class='jf-muted-note' style='margin-top:8px'>{esc(snippet)}</div>"
        if snippet else ""
    )

    with st.container(border=True, key=f"card_history_{index}"):
        html_block(
            f"""
            <div class="jf-match-head">
                <div class="jf-job-logo" style="background:var(--jf-teal-soft);color:var(--jf-teal-dark)">📄</div>
                <div class="grow">
                    <div class="jf-job-title" style="font-size:1.05rem">{esc(filename)}</div>
                    <div class="jf-job-company">🕒 {esc(created_at)}</div>
                    {snippet_html}
                </div>
                <div style="text-align:center">
                    {score_ring(score)}
                    <div class="jf-muted-note" style="margin-top:4px">Match Score</div>
                </div>
            </div>
            """
        )

        with st.expander("Lihat detail analisis"):
            html_block(
                meter(
                    "Skill Overlap",
                    float(item.get("skill_overlap_ratio") or 0),
                    "var(--jf-teal)",
                )
                + meter(
                    "Semantic Similarity",
                    float(item.get("semantic_similarity") or 0),
                    "var(--jf-purple)",
                )
                + meter("Match Score", score, "var(--jf-coral)")
            )

            html_block(
                "<div class='jf-panel'><h4>Insight</h4><p>"
                + text_to_html(item.get("explanation") or "-")
                + "</p></div>"
            )

            st.write("")

            col_a, col_b = st.columns(2)

            with col_a:
                html_block(
                    "<div class='jf-panel'><h4>✅ Skill yang Cocok</h4>"
                    + skills_html(
                        item.get("matched_skills"),
                        "Belum ada skill yang cocok secara eksplisit.",
                        "teal",
                    )
                    + "</div>"
                )

            with col_b:
                html_block(
                    "<div class='jf-panel'><h4>⚠️ Skill yang Belum Terlihat</h4>"
                    + skills_html(
                        item.get("missing_skills"),
                        "Tidak ada gap requirement yang signifikan.",
                        "coral",
                    )
                    + "</div>"
                )


def run_cv_screening():
    page_header(
        "CV",
        "Screening",
        "Upload CV dan masukkan deskripsi pekerjaan untuk menilai "
        "kecocokan kandidat dengan posisi yang dilamar.",
        badge="Analisis AI",
    )

    if using_trained_vocab() and ml_model.is_model_available():
        st.caption(
            f"Model ML aktif — {skill_vocab_size()} skill dikenali."
        )
    else:
        st.caption(
            "Model ML belum ditemukan. Sistem menggunakan fallback."
        )

    with st.container(border=True, key="card_inputs"):
        col_left, col_right = st.columns(2, gap="large")

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

        analyze_clicked = st.button(
            "Analisis CV",
            type="primary",
            use_container_width=True,
        )

    # Analisis CV sekaligus menyimpan hasil ke riwayat
    if analyze_clicked:
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
        section_title("Hasil Analisis Terbaru")

        final_score = saved_result["final_score"]

        if final_score >= 75:
            tone, verdict = (
                "good",
                "Sangat direkomendasikan — kandidat sangat sesuai.",
            )
        elif final_score >= 50:
            tone, verdict = (
                "mid",
                "Layak dipertimbangkan — masih ada beberapa gap.",
            )
        else:
            tone, verdict = (
                "low",
                "Kurang sesuai — terdapat gap yang signifikan.",
            )

        hero_col, detail_col = st.columns([1, 1.3], gap="large")

        with hero_col:
            html_block(
                f"""
                <div class="jf-score-hero jf-verdict-{tone}">
                    <small>Match Score</small>
                    <div class="v">{final_score:.1f}<span>%</span></div>
                    <div class="t">{esc(verdict)}</div>
                </div>
                """
            )

        with detail_col:
            html_block(
                "<div class='jf-panel'><h4>Breakdown Skor</h4>"
                + meter(
                    "Skill Overlap",
                    saved_result["skill_overlap_ratio"],
                    "var(--jf-teal)",
                )
                + meter(
                    "Semantic Similarity",
                    saved_result["semantic_similarity"],
                    "var(--jf-purple)",
                )
                + meter("Match Score", final_score, "var(--jf-coral)")
                + "</div>"
            )

        st.write("")

        html_block(
            "<div class='jf-panel'><h4>Insight</h4><p>"
            + text_to_html(saved_result["explanation"])
            + "</p></div>"
        )

        st.write("")

        col_a, col_b = st.columns(2)

        with col_a:
            html_block(
                "<div class='jf-panel'><h4>✅ Skill yang Cocok</h4>"
                + skills_html(
                    saved_result["matched_skills"],
                    "Belum ada skill yang cocok secara eksplisit.",
                    "teal",
                )
                + "</div>"
            )

        with col_b:
            html_block(
                "<div class='jf-panel'><h4>⚠️ Skill yang Belum Terlihat</h4>"
                + skills_html(
                    saved_result["missing_skills"],
                    "Tidak ada gap requirement yang signifikan.",
                    "coral",
                )
                + "</div>"
            )

        html_block(
            "<div class='jf-info'>Hasil ini merupakan alat bantu "
            "pengambilan keputusan, bukan pengganti penilaian "
            "rekruter.</div>"
        )

    # =========================================================
    # RIWAYAT ANALISIS
    # =========================================================
    section_title("Riwayat CV Screening")
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
