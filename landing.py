"""
landing.py
----------
Halaman depan Jobify (sebelum login): navbar, hero, fitur, cara kerja.
"""

import json
import os

import pandas as pd
import streamlit as st

from ui import esc, html_block, logo

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


@st.cache_data(show_spinner=False)
def _catalog_stats():
    """Angka nyata dari katalog lokal, bukan angka karangan."""
    jobs = 0
    skills = 0

    try:
        path = os.path.join(BASE_DIR, "data", "jobs_processed.csv")
        jobs = len(pd.read_csv(path, usecols=["job_id"]))
    except Exception:
        pass

    try:
        path = os.path.join(BASE_DIR, "models", "skill_vocab.json")
        with open(path, "r", encoding="utf-8") as f:
            skills = len(json.load(f))
    except Exception:
        pass

    return jobs, skills


def _open_auth(mode):
    st.session_state["view"] = "auth"
    st.session_state["auth_mode"] = mode


def render_navbar(show_back=False):
    """Navbar atas: logo di kiri, tautan dan tombol Masuk di kanan."""
    col_logo, col_links, col_btn = st.columns([4, 3, 1.3], vertical_alignment="center")

    with col_logo:
        html_block(logo())

    if show_back:
        with col_btn:
            st.button(
                "← Beranda",
                key="nav_back",
                use_container_width=True,
                on_click=lambda: st.session_state.update(view="landing"),
            )
        return

    with col_links:
        html_block(
            """
            <div class="jf-navlinks">
                <a href="#fitur">Fitur</a>
                <a href="#tentang">Tentang</a>
            </div>
            """
        )

    with col_btn:
        st.button(
            "Masuk",
            key="nav_login",
            use_container_width=True,
            on_click=_open_auth,
            args=("Masuk",),
        )


def render_landing():
    jobs_count, skills_count = _catalog_stats()

    render_navbar()

    st.write("")
    st.write("")

    left, right = st.columns([1.05, 1], gap="large", vertical_alignment="center")

    # ---------------------- Kiri: teks hero ----------------------
    with left:
        html_block(
            """
            <span class="jf-badge">Platform Karier Berbasis AI</span>
            <h1 class="jf-hero-title">Temukan<br><span class="acc">Karir Impian</span><br>Kamu Sekarang</h1>
            <p class="jf-hero-desc">Analisis CV otomatis, pencocokan karir cerdas, dan ribuan lowongan terkurasi — semua dalam satu platform.</p>
            """
        )

        b1, b2, _ = st.columns([1.1, 1.1, 1.4])

        with b1:
            st.button(
                "Mulai Gratis",
                key="cta_start",
                type="primary",
                use_container_width=True,
                on_click=_open_auth,
                args=("Daftar",),
            )

        with b2:
            html_block(
                "<a class='jf-cta-link' href='#fitur' "
                "style='width:100%'>Lihat Demo</a>"
            )

        jobs_label = f"{jobs_count:,}+" if jobs_count else "Ribuan"
        skills_label = f"{skills_count:,}" if skills_count else "Ratusan"

        html_block(
            f"""
            <div class="jf-stats">
                <div><div class="jf-stat-num">{esc(jobs_label)}</div><div class="jf-stat-lbl">Lowongan Aktif</div></div>
                <div><div class="jf-stat-num">{esc(skills_label)}</div><div class="jf-stat-lbl">Skill Dikenali</div></div>
                <div><div class="jf-stat-num">Gratis</div><div class="jf-stat-lbl">Untuk Pencari Kerja</div></div>
            </div>
            """
        )

    # ---------------------- Kanan: kartu mengambang ----------------------
    with right:
        html_block(
            f"""
            <div class="jf-float-wrap">
                <div class="jf-fcard jf-fcard-teal">
                    <small>CV Match Score</small>
                    <div class="big">87<span>%</span></div>
                    <div class="role">Senior Frontend Developer @ Tokopedia</div>
                    <div class="jf-bar"><i></i></div>
                    <span class="jf-fchip">React</span><span class="jf-fchip">TypeScript</span><span class="jf-fchip">CSS</span>
                </div>
                <div class="jf-fcard jf-fcard-coral">
                    <small>Career Match</small>
                    <div class="mid">5 Pekerjaan</div>
                    <div class="sub">cocok dengan CV kamu</div>
                    <div class="jf-avs"><b>T</b><b>G</b><b>S</b><b>B</b></div>
                </div>
                <div class="jf-fcard jf-fcard-white">
                    <div class="ico">🎯</div>
                    <div><b>NLP Skill Extraction</b><span>Skill diekstrak dari CV kamu secara otomatis</span></div>
                </div>
                <div class="jf-fcard jf-fcard-purple">
                    <small>Katalog Skill</small>
                    <div class="mid">{esc(skills_label)}</div>
                    <div class="sub">skill dikenali</div>
                </div>
            </div>
            """
        )

    # ---------------------- Fitur ----------------------
    html_block(
        """
        <div id="fitur" class="jf-feat-grid" style="margin-top:2.2rem;scroll-margin-top:20px">
            <div class="jf-feat jf-feat-teal"><span class="ico">📄</span><h4>CV Screening</h4><p>Analisis kecocokan CV kamu dengan satu lowongan secara instan</p></div>
            <div class="jf-feat jf-feat-coral"><span class="ico">⚡</span><h4>Career Match</h4><p>Temukan lowongan terbaik dari seluruh katalog berdasarkan CV kamu</p></div>
            <div class="jf-feat jf-feat-amber"><span class="ico">🔍</span><h4>Cari Lowongan</h4><p>Eksplorasi ribuan lowongan dengan filter lokasi, jenis, dan pendidikan</p></div>
            <div class="jf-feat jf-feat-purple"><span class="ico">🤖</span><h4>AI Skill Extract</h4><p>NLP otomatis ekstrak skill dari CV dan deskripsi pekerjaan</p></div>
        </div>
        """
    )

    # ---------------------- Tentang / cara kerja ----------------------
    html_block(
        """
        <div id="tentang" class="jf-section-head" style="scroll-margin-top:20px">
            <span class="jf-badge">Cara Kerja</span>
            <h2>Dari CV ke <span class="acc">lowongan yang tepat</span></h2>
            <p>Tiga langkah singkat, tanpa perlu mengisi formulir panjang.</p>
        </div>
        <div class="jf-steps">
            <div class="jf-step"><div class="n" style="background:var(--jf-teal)">1</div><h4>Upload CV (PDF)</h4><p>Unggah CV kamu. Teks dibaca otomatis, tidak perlu diketik ulang.</p></div>
            <div class="jf-step"><div class="n" style="background:var(--jf-coral)">2</div><h4>AI membaca skill</h4><p>Skill diekstrak dari CV lalu dibandingkan dengan lowongan yang tersedia.</p></div>
            <div class="jf-step"><div class="n" style="background:var(--jf-purple)">3</div><h4>Lihat hasil &amp; gap skill</h4><p>Dapatkan skor kecocokan, skill yang sudah cocok, dan yang masih perlu dipelajari.</p></div>
        </div>
        """
    )

    with st.container(key="cta_band"):
        html_block(
            """
            <h3>Siap menemukan karir impianmu?</h3>
            <p class="cta-t">Buat akun gratis dan mulai analisis CV pertamamu.</p>
            """
        )

        _, cta_col, _ = st.columns([1.3, 1, 1.3])

        with cta_col:
            st.button(
                "Daftar Sekarang",
                key="cta_bottom",
                use_container_width=True,
                on_click=_open_auth,
                args=("Daftar",),
            )

    html_block(
        "<div class='jf-footer'>© Jobify — skor kecocokan adalah alat bantu, "
        "bukan pengganti penilaian rekruter.</div>"
    )
