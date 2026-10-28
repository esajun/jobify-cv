"""
ui.py
-----
Design system Jobify: CSS global + komponen HTML kecil yang dipakai
di seluruh halaman, supaya tampilan konsisten.

Palet warna mengikuti referensi desain:
teal (utama), coral, ungu, dan krem dengan latar biru-abu sangat muda.
"""

import html
import json

import streamlit as st

# ==================================================
# CSS GLOBAL
# ==================================================

_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&display=swap');

:root {
    --jf-teal: #12A383;
    --jf-teal-dark: #0E8A6E;
    --jf-teal-soft: #E8F7F2;
    --jf-coral: #FF6B6B;
    --jf-coral-soft: #FFF0F0;
    --jf-amber: #E08A00;
    --jf-cream: #FFF5E6;
    --jf-purple: #7C5CBF;
    --jf-lav: #EFEBFA;
    --jf-ink: #1A1D2E;
    --jf-muted: #5F667A;
    --jf-line: #E3E8F1;
    --jf-bg: #F6F8FC;
    --jf-card: #FFFFFF;
    --jf-shadow: 0 8px 28px rgba(26, 29, 46, 0.07);
}

/* ---------- Dasar ---------- */
.stApp {
    background: var(--jf-bg);
    color: var(--jf-ink);
    font-family: 'Outfit', system-ui, -apple-system, 'Segoe UI', sans-serif;
}
.stApp :is(p, h1, h2, h3, h4, h5, h6, label, li, input, textarea, button, a, th, td, summary) {
    font-family: 'Outfit', system-ui, -apple-system, 'Segoe UI', sans-serif;
}
#MainMenu, footer,
[data-testid="stDecoration"],
[data-testid="stToolbar"],
[data-testid="stSidebar"],
[data-testid="stSidebarNav"],
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"] {
    display: none !important;
}
header[data-testid="stHeader"] {
    background: transparent;
    height: 0;
}
.block-container {
    max-width: 1240px;
    padding: 1.1rem 2rem 4rem !important;
}
html { scroll-behavior: smooth; }

h1, h2, h3, h4 {
    color: var(--jf-ink);
    letter-spacing: -0.02em;
    font-weight: 700;
}
h1 { font-weight: 800; }
[data-testid="stCaptionContainer"],
.stApp small { color: var(--jf-muted); }
hr { border-color: var(--jf-line) !important; }

/* ---------- Tombol ---------- */
.stButton > button,
.stFormSubmitButton > button,
.stDownloadButton > button,
[data-testid="stBaseLinkButton-secondary"],
[data-testid="stBaseLinkButton-primary"] {
    border-radius: 12px;
    font-weight: 600;
    font-size: 0.95rem;
    min-height: 2.9rem;
    padding: 0.55rem 1.4rem;
    transition: transform .15s ease, box-shadow .15s ease, background .15s ease;
}
[data-testid="stBaseButton-primary"],
[data-testid="stBaseButton-primaryFormSubmit"],
[data-testid="stBaseLinkButton-primary"] {
    background: var(--jf-teal);
    border: 1.5px solid var(--jf-teal);
    color: #fff;
}
[data-testid="stBaseButton-primary"]:hover,
[data-testid="stBaseButton-primaryFormSubmit"]:hover,
[data-testid="stBaseLinkButton-primary"]:hover {
    background: var(--jf-teal-dark);
    border-color: var(--jf-teal-dark);
    color: #fff;
    transform: translateY(-1px);
    box-shadow: 0 8px 18px rgba(18, 163, 131, 0.28);
}
[data-testid="stBaseButton-secondary"],
[data-testid="stBaseButton-secondaryFormSubmit"],
[data-testid="stBaseLinkButton-secondary"] {
    background: #fff;
    border: 1.5px solid var(--jf-ink);
    color: var(--jf-ink);
}
[data-testid="stBaseButton-secondary"]:hover,
[data-testid="stBaseButton-secondaryFormSubmit"]:hover,
[data-testid="stBaseLinkButton-secondary"]:hover {
    background: var(--jf-ink);
    border-color: var(--jf-ink);
    color: #fff;
    transform: translateY(-1px);
}
.stButton > button:disabled {
    background: #fff;
    border-color: var(--jf-line);
    color: #A3AABC;
    transform: none;
    box-shadow: none;
}
.stButton > button p { font-weight: 600; }

/* ---------- Input ---------- */
[data-baseweb="input"],
[data-baseweb="textarea"],
[data-baseweb="select"] > div {
    background: #fff;
    border: 1.5px solid var(--jf-line);
    border-radius: 12px;
    transition: border-color .15s ease, box-shadow .15s ease;
}
[data-baseweb="input"]:focus-within,
[data-baseweb="textarea"]:focus-within,
[data-baseweb="select"] > div:focus-within {
    border-color: var(--jf-teal);
    box-shadow: 0 0 0 3px rgba(18, 163, 131, 0.15);
}
[data-baseweb="base-input"], [data-baseweb="input"] input, [data-baseweb="textarea"] textarea,
[data-baseweb="select"] > div > div {
    background: #fff !important;
    border-radius: 12px;
}
[data-testid="stWidgetLabel"] p,
.stApp label p {
    font-weight: 600;
    font-size: 0.88rem;
    color: var(--jf-ink);
}

/* ---------- Form, kartu, expander ---------- */
[data-testid="stForm"] {
    background: #fff;
    border: 1.5px solid var(--jf-line);
    border-radius: 20px;
    padding: 1.4rem 1.4rem 1.2rem;
    box-shadow: var(--jf-shadow);
}
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"] .jf-card-marker),
[class*="st-key-card"] {
    background: #fff;
    border: 1.5px solid var(--jf-line);
    border-radius: 20px;
    box-shadow: var(--jf-shadow);
    padding: 0.9rem 1rem;
}
[data-testid="stExpander"] {
    background: #fff;
    border: 1.5px solid var(--jf-line);
    border-radius: 14px;
    overflow: hidden;
}
[data-testid="stExpander"] details { border: none; }
[data-testid="stExpander"] summary { font-weight: 600; }
[data-testid="stAlert"] {
    border-radius: 14px;
    border: none;
}
[data-testid="stFileUploaderDropzone"] {
    background: var(--jf-teal-soft);
    border: 2px dashed rgba(18, 163, 131, 0.55);
    border-radius: 18px;
    padding: 1.4rem;
}
[data-testid="stFileUploaderDropzone"]:hover { background: #DDF3EC; }
[data-testid="stProgress"] [role="progressbar"] > div { background: var(--jf-teal); }

/* ---------- Tab & kontrol segmen ---------- */
[data-testid="stTabs"] [role="tablist"] {
    gap: 6px;
    background: #fff;
    border: 1.5px solid var(--jf-line);
    border-radius: 14px;
    padding: 5px;
    width: fit-content;
}
[data-testid="stTabs"] [role="tab"] {
    border-radius: 10px;
    padding: 0.45rem 1.1rem;
    height: auto;
    font-weight: 600;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background: var(--jf-teal);
    color: #fff;
}
[data-testid="stTabs"] [aria-selected="true"] p { color: #fff; }
[data-testid="stTabs"] [data-baseweb="tab-highlight"],
[data-testid="stTabs"] [data-baseweb="tab-border"] { display: none; }
[data-testid="stDataFrame"] {
    border: 1.5px solid var(--jf-line);
    border-radius: 16px;
    overflow: hidden;
}
[data-testid="stMetric"] {
    background: #fff;
    border: 1.5px solid var(--jf-line);
    border-radius: 18px;
    padding: 1rem 1.2rem;
}
[data-testid="stMetricValue"] { font-weight: 800; letter-spacing: -0.02em; }

/* ---------- Logo & navbar ---------- */
.jf-logo {
    display: flex; align-items: center; gap: 10px;
    font-weight: 800; font-size: 1.15rem; color: var(--jf-ink);
    letter-spacing: -0.01em; height: 2.9rem;
}
.jf-logo-mark {
    width: 32px; height: 32px; border-radius: 9px;
    background: var(--jf-teal); color: #fff;
    display: grid; place-items: center; font-size: 1rem; font-weight: 800;
}
.jf-navlinks {
    display: flex; justify-content: flex-end; align-items: center;
    gap: 26px; height: 2.9rem; padding-right: 18px;
}
.jf-navlinks a {
    color: var(--jf-ink) !important; text-decoration: none !important;
    font-size: 0.82rem; font-weight: 600;
}
.jf-navlinks a:hover { color: var(--jf-teal) !important; }
.st-key-nav_login button,
.st-key-nav_back button {
    min-height: 2.6rem;
    padding: 0.4rem 1.2rem;
    border-radius: 12px;
}
.st-key-nav_login button {
    background: var(--jf-ink); border-color: var(--jf-ink); color: #fff;
}
.st-key-nav_login button:hover {
    background: #000; border-color: #000; color: #fff;
}
.st-key-appnav {
    background: #fff;
    border: 1.5px solid var(--jf-line);
    border-radius: 18px;
    padding: 0.55rem 1rem;
    box-shadow: var(--jf-shadow);
    margin-bottom: 1.4rem;
}
.st-key-appnav [data-testid="stBaseButton-secondary"] {
    border: none; background: transparent; color: var(--jf-muted);
    min-height: 2.6rem;
}
.st-key-appnav [data-testid="stBaseButton-secondary"]:hover {
    background: var(--jf-teal-soft); color: var(--jf-teal-dark); transform: none;
}
.st-key-appnav [data-testid="stBaseButton-primary"] {
    min-height: 2.6rem;
    background: var(--jf-teal-soft); color: var(--jf-teal-dark);
    border-color: var(--jf-teal-soft); box-shadow: none;
}
.st-key-appnav .st-key-logout_user button,
.st-key-appnav .st-key-logout_admin button {
    border: 1.5px solid var(--jf-line); color: var(--jf-ink); background: #fff;
}
.st-key-appnav .st-key-logout_user button:hover,
.st-key-appnav .st-key-logout_admin button:hover {
    background: var(--jf-coral-soft); border-color: var(--jf-coral); color: #D64545;
}
.jf-user {
    display: flex; align-items: center; justify-content: flex-end; gap: 10px;
    height: 2.6rem; font-weight: 600; font-size: 0.9rem;
}
.jf-avatar {
    width: 34px; height: 34px; border-radius: 50%;
    background: var(--jf-teal); color: #fff;
    display: grid; place-items: center; font-weight: 700; font-size: 0.9rem;
}
.jf-role-pill {
    background: var(--jf-lav); color: var(--jf-purple);
    border-radius: 999px; padding: 4px 12px; font-size: 0.75rem; font-weight: 700;
}

/* ---------- Hero ---------- */
.jf-badge {
    display: inline-flex; align-items: center; gap: 8px;
    background: var(--jf-teal-soft); color: var(--jf-teal-dark);
    border-radius: 999px; padding: 7px 16px;
    font-size: 0.78rem; font-weight: 700;
}
.jf-badge::before {
    content: ""; width: 7px; height: 7px; border-radius: 50%;
    background: var(--jf-teal);
}
.jf-hero-title {
    font-size: clamp(2.6rem, 5vw, 3.7rem); line-height: 1.08;
    font-weight: 800; letter-spacing: -0.03em;
    margin: 1.1rem 0 1.3rem; color: var(--jf-ink);
}
.stApp h1.jf-hero-title { color: var(--jf-ink); }
.stApp h1.jf-hero-title .acc { color: var(--jf-teal); }
.jf-hero-desc {
    font-size: 1.05rem; line-height: 1.65; color: #3A4056; max-width: 460px;
}
.jf-stats { display: flex; gap: 2.2rem; margin-top: 1.9rem; }
.jf-stat-num { font-size: 1.5rem; font-weight: 800; letter-spacing: -0.02em; }
.jf-stat-lbl { font-size: 0.8rem; color: var(--jf-muted); }

.jf-cta-link {
    display: inline-flex; align-items: center; justify-content: center;
    min-height: 2.9rem; padding: 0.55rem 1.5rem; border-radius: 12px;
    border: 1.5px solid var(--jf-ink); background: #fff;
    color: var(--jf-ink) !important; font-weight: 600; font-size: 0.95rem;
    text-decoration: none !important; transition: all .15s ease;
}
.jf-cta-link:hover { background: var(--jf-ink); color: #fff !important; transform: translateY(-1px); }

.jf-float-wrap { position: relative; height: 470px; max-width: 560px; margin-left: auto; }
.jf-fcard {
    position: absolute; border-radius: 24px; color: #fff;
    box-shadow: 0 18px 40px rgba(26, 29, 46, 0.16);
    animation: jf-float 6s ease-in-out infinite;
}
.stApp .jf-fcard small, .stApp .jf-statcard small, .stApp .jf-score-hero small { color: #fff !important; }
.jf-fcard small { display: block; font-size: 0.7rem; font-weight: 600; opacity: .85; }
.jf-fcard-teal {
    top: 0; right: 20px; width: 250px; padding: 22px 22px 20px;
    background: var(--jf-teal);
}
.jf-fcard-teal .big { font-size: 3.6rem; font-weight: 800; line-height: 1; margin: 8px 0 6px; letter-spacing: -0.03em; }
.jf-fcard-teal .big span { font-size: 1.6rem; }
.jf-fcard-teal .role { font-size: 0.82rem; opacity: .9; line-height: 1.4; }
.jf-bar { height: 6px; border-radius: 99px; background: rgba(255,255,255,.3); margin: 14px 0 12px; overflow: hidden; }
.jf-bar i { display: block; height: 100%; width: 87%; background: #fff; border-radius: 99px; }
.jf-fchip {
    display: inline-block; background: rgba(255,255,255,.22); border-radius: 99px;
    padding: 3px 11px; font-size: 0.68rem; font-weight: 700; margin-right: 6px;
}
.jf-fcard-coral {
    top: 172px; left: 20px; width: 215px; padding: 20px;
    background: var(--jf-coral); animation-delay: -2s;
}
.jf-fcard-coral .mid { font-size: 1.55rem; font-weight: 800; margin: 6px 0 2px; letter-spacing: -0.02em; }
.jf-fcard-coral .sub { font-size: 0.7rem; opacity: .9; }
.jf-avs { display: flex; margin-top: 12px; }
.jf-avs b {
    width: 28px; height: 28px; border-radius: 50%; margin-right: -7px;
    background: rgba(255,255,255,.3); border: 2px solid rgba(255,255,255,.6);
    display: grid; place-items: center; font-size: 0.65rem;
}
.jf-fcard-white {
    top: 300px; right: 20px; width: 225px; padding: 16px 18px;
    background: #fff; color: var(--jf-ink); display: flex; gap: 12px; align-items: center;
    animation-delay: -4s;
}
.jf-fcard-white .ico {
    width: 36px; height: 36px; border-radius: 10px; background: var(--jf-coral-soft);
    display: grid; place-items: center; font-size: 1.1rem; flex: none;
}
.jf-fcard-white b { font-size: 0.78rem; display: block; }
.jf-fcard-white span { font-size: 0.68rem; color: var(--jf-muted); line-height: 1.35; display: block; margin-top: 2px; }
.jf-fcard-purple {
    top: 365px; left: -22px; width: 160px; padding: 18px 20px;
    background: var(--jf-purple); animation-delay: -1s;
}
.jf-fcard-purple .mid { font-size: 1.9rem; font-weight: 800; letter-spacing: -0.02em; margin: 4px 0 2px; }
.jf-fcard-purple .sub { font-size: 0.7rem; opacity: .85; }
@keyframes jf-float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-8px); }
}

/* ---------- Kartu fitur ---------- */
.jf-feat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 18px; margin-top: 0.6rem; }
.jf-feat { border-radius: 22px; padding: 24px 22px 26px; transition: transform .2s ease, box-shadow .2s ease; }
.jf-feat:hover { transform: translateY(-4px); box-shadow: var(--jf-shadow); }
.jf-feat .ico { font-size: 1.7rem; margin-bottom: 14px; display: block; }
.jf-feat h4 { margin: 0 0 8px; font-size: 1.05rem; font-weight: 800; }
.jf-feat p { margin: 0; font-size: 0.85rem; line-height: 1.6; color: #3A4056; }
.jf-feat-teal { background: var(--jf-teal-soft); } .jf-feat-teal h4 { color: var(--jf-teal); }
.jf-feat-coral { background: var(--jf-coral-soft); } .jf-feat-coral h4 { color: var(--jf-coral); }
.jf-feat-amber { background: var(--jf-cream); } .jf-feat-amber h4 { color: var(--jf-amber); }
.jf-feat-purple { background: var(--jf-lav); } .jf-feat-purple h4 { color: var(--jf-purple); }

.jf-section-head { text-align: center; margin: 4.5rem 0 2rem; }
.jf-section-head h2 { font-size: 2.2rem; font-weight: 800; margin: 0.9rem 0 0.4rem; }
.jf-section-head h2 .acc { color: var(--jf-teal); }
.jf-section-head p { color: var(--jf-muted); margin: 0; }

.jf-steps { display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; }
.jf-step {
    background: #fff; border: 1.5px solid var(--jf-line); border-radius: 22px; padding: 26px;
}
.jf-step .n {
    width: 38px; height: 38px; border-radius: 12px; display: grid; place-items: center;
    font-weight: 800; color: #fff; margin-bottom: 14px;
}
.jf-step h4 { margin: 0 0 6px; font-size: 1.1rem; }
.jf-step p { margin: 0; color: var(--jf-muted); font-size: 0.9rem; line-height: 1.6; }

.st-key-cta_band {
    margin-top: 2.2rem; border-radius: 26px; padding: 2.4rem 2rem; text-align: center;
    background: linear-gradient(135deg, var(--jf-teal) 0%, #0B7F67 100%);
}
.st-key-cta_band h3 { color: #fff; font-size: 1.7rem; font-weight: 800; margin: 0 0 6px; }
.st-key-cta_band .cta-t { margin: 0 0 1rem; color: rgba(255,255,255,.92); }
.st-key-cta_band [data-testid="stMarkdownContainer"] { text-align: center; }
.st-key-cta_band [data-testid="stBaseButton-secondary"] p { color: var(--jf-teal-dark); }
.st-key-cta_band [data-testid="stBaseButton-secondary"]:hover p { color: #fff; }
.st-key-cta_band [data-testid="stBaseButton-secondary"] {
    background: #fff; color: var(--jf-teal-dark); border-color: #fff;
}
.st-key-cta_band [data-testid="stBaseButton-secondary"]:hover {
    background: var(--jf-ink); color: #fff; border-color: var(--jf-ink);
}
.jf-footer { text-align: center; color: var(--jf-muted); font-size: 0.8rem; margin-top: 3rem; }

/* ---------- Halaman login ---------- */
.jf-auth-side {
    background: linear-gradient(150deg, var(--jf-teal) 0%, #0B7F67 100%);
    border-radius: 28px; padding: 2.6rem 2.2rem; color: #fff; min-height: 520px;
    position: relative; overflow: hidden;
}
.jf-auth-side::after {
    content: ""; position: absolute; width: 260px; height: 260px; border-radius: 50%;
    background: rgba(255,255,255,.08); right: -80px; bottom: -80px;
}
.jf-auth-side h2 { color: #fff; font-size: 2.1rem; line-height: 1.15; margin: 1.2rem 0 0.8rem; font-weight: 800; }
.jf-auth-side p { opacity: .92; line-height: 1.6; max-width: 380px; }
.jf-auth-points { list-style: none; padding: 0; margin: 1.6rem 0 0; display: grid; gap: 12px; }
.jf-auth-points li {
    background: rgba(255,255,255,.14); border-radius: 14px; padding: 12px 16px;
    font-size: 0.9rem; font-weight: 500; display: flex; gap: 12px; align-items: center;
}
.jf-auth-form-head h3 { font-size: 1.7rem; font-weight: 800; margin: 0 0 4px; }
.jf-auth-form-head p { color: var(--jf-muted); margin: 0 0 1.1rem; }
.st-key-auth_mode [data-testid="stSegmentedControl"] button { font-weight: 600; }

/* ---------- Header halaman ---------- */
.jf-page-head { margin: 0.4rem 0 1.4rem; }
.jf-page-head h1 {
    font-size: 2.4rem; line-height: 1.12; margin: 0.8rem 0 0.4rem;
    font-weight: 800; letter-spacing: -0.03em;
}
.stApp .jf-page-head h1 { color: var(--jf-ink); }
.stApp .jf-page-head h1 .acc { color: var(--jf-teal); }
.jf-page-head p { margin: 0; color: var(--jf-muted); font-size: 1rem; }

.jf-section-title {
    display: flex; align-items: center; gap: 10px;
    font-size: 1.25rem; font-weight: 800; letter-spacing: -0.02em; margin: 1.6rem 0 0.8rem;
}
.jf-section-title::before {
    content: ""; width: 8px; height: 24px; border-radius: 4px; background: var(--jf-teal);
}

/* ---------- Kartu statistik ---------- */
.jf-stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 16px; margin: 0.4rem 0 1rem; }
.jf-statcard { border-radius: 22px; padding: 20px 22px; color: #fff; box-shadow: var(--jf-shadow); }
.jf-statcard small { display: block; font-size: 0.78rem; font-weight: 600; opacity: .88; }
.jf-statcard .v { font-size: 2.3rem; font-weight: 800; letter-spacing: -0.03em; line-height: 1.1; margin: 6px 0 4px; }
.jf-statcard .c { font-size: 0.78rem; opacity: .85; }
.jf-tone-teal { background: var(--jf-teal); }
.jf-tone-coral { background: var(--jf-coral); }
.jf-tone-purple { background: var(--jf-purple); }
.jf-tone-amber { background: #F2A21B; }
.jf-tone-ink { background: var(--jf-ink); }

/* ---------- Chip ---------- */
.jf-chips { display: flex; flex-wrap: wrap; gap: 7px; margin: 8px 0; }
.jf-chip {
    display: inline-flex; align-items: center; gap: 5px;
    border-radius: 999px; padding: 5px 12px; font-size: 0.76rem; font-weight: 600;
    background: #F1F4F9; color: #3A4056;
}
.jf-chip-teal { background: var(--jf-teal-soft); color: var(--jf-teal-dark); }
.jf-chip-coral { background: var(--jf-coral-soft); color: #D64545; }
.jf-chip-amber { background: var(--jf-cream); color: #B86E00; }
.jf-chip-purple { background: var(--jf-lav); color: var(--jf-purple); }

/* ---------- Kartu lowongan ---------- */
.jf-job { display: flex; gap: 16px; align-items: flex-start; }
.jf-job-logo {
    width: 52px; height: 52px; border-radius: 16px; flex: none;
    display: grid; place-items: center; font-weight: 800; font-size: 1.3rem;
}
.jf-job-main { flex: 1; min-width: 0; }
.jf-job-title { font-size: 1.2rem; font-weight: 800; letter-spacing: -0.02em; line-height: 1.25; }
.jf-job-company { color: var(--jf-muted); font-weight: 500; font-size: 0.92rem; margin-top: 2px; }
.jf-job-salary { font-weight: 700; color: var(--jf-teal-dark); font-size: 0.95rem; white-space: nowrap; }

/* ---------- Skor ---------- */
.jf-ring {
    --p: 0; --c: var(--jf-teal);
    width: 78px; height: 78px; border-radius: 50%; flex: none;
    background: conic-gradient(var(--c) calc(var(--p) * 1%), #E9EDF4 0);
    display: grid; place-items: center; position: relative;
}
.jf-ring::before { content: ""; position: absolute; inset: 8px; background: #fff; border-radius: 50%; }
.jf-ring b { position: relative; font-size: 1.05rem; font-weight: 800; letter-spacing: -0.02em; }
.jf-rank {
    width: 40px; height: 40px; border-radius: 12px; flex: none;
    display: grid; place-items: center; font-weight: 800; color: #fff; background: var(--jf-ink);
}
.jf-rank-1 { background: var(--jf-teal); }
.jf-rank-2 { background: var(--jf-coral); }
.jf-rank-3 { background: var(--jf-purple); }
.jf-match-head { display: flex; gap: 16px; align-items: center; }
.jf-match-head .grow { flex: 1; min-width: 0; }
.jf-meter { margin: 14px 0; }
.jf-meter .row { display: flex; justify-content: space-between; font-size: 0.85rem; font-weight: 600; margin-bottom: 6px; }
.jf-meter .track { height: 10px; border-radius: 99px; background: #E9EDF4; overflow: hidden; }
.jf-meter .fill { height: 100%; border-radius: 99px; }

.jf-score-hero { border-radius: 26px; padding: 26px 28px; color: #fff; box-shadow: var(--jf-shadow); }
.jf-score-hero small { font-weight: 600; opacity: .9; font-size: 0.85rem; }
.jf-score-hero .v { font-size: 4.4rem; font-weight: 800; letter-spacing: -0.04em; line-height: 1; margin: 8px 0; }
.jf-score-hero .v span { font-size: 2rem; }
.jf-score-hero .t { font-size: 0.95rem; opacity: .95; line-height: 1.5; }
.jf-verdict-good { background: var(--jf-teal); }
.jf-verdict-mid { background: #F2A21B; }
.jf-verdict-low { background: var(--jf-coral); }

.jf-panel { background: #fff; border: 1.5px solid var(--jf-line); border-radius: 20px; padding: 20px 22px; }
.jf-panel h4 { margin: 0 0 10px; font-size: 1rem; font-weight: 800; }
.jf-panel p { margin: 0; color: #3A4056; line-height: 1.65; font-size: 0.92rem; }
.jf-muted-note { color: var(--jf-muted); font-size: 0.85rem; }
.jf-info {
    background: var(--jf-lav); color: #4B3A82; border-radius: 14px;
    padding: 12px 16px; font-size: 0.86rem; font-weight: 500; margin-top: 1rem;
}
details.jf-details {
    border: 1.5px solid var(--jf-line); border-radius: 14px; padding: 4px 16px; margin: 10px 0; background: #FBFCFE;
}
details.jf-details summary { cursor: pointer; font-weight: 700; padding: 10px 0; font-size: 0.92rem; }
details.jf-details div { font-size: 0.9rem; line-height: 1.7; color: #3A4056; padding: 0 0 12px; }
.jf-empty {
    text-align: center; background: #fff; border: 1.5px dashed var(--jf-line);
    border-radius: 20px; padding: 2.4rem 1rem; color: var(--jf-muted);
}
.jf-pager { text-align: center; padding-top: 10px; font-weight: 500; color: var(--jf-muted); }
.jf-pager b { color: var(--jf-ink); }

[data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="base-input"],
[data-baseweb="textarea"] textarea { background: #fff !important; }

/* ---------- Responsif ---------- */
@media (max-width: 900px) {
    .block-container { padding: 1rem 1rem 3rem !important; }
    .jf-feat-grid, .jf-steps { grid-template-columns: 1fr 1fr; }
    .jf-float-wrap { margin: 2rem auto 0; transform: scale(.9); transform-origin: top center; }
    .jf-navlinks { display: none; }
}
@media (max-width: 560px) {
    .jf-feat-grid, .jf-steps { grid-template-columns: 1fr; }
    .jf-stats { gap: 1.4rem; }
}
"""


def inject_css():
    """Pasang tema Jobify. Panggil sekali di awal setiap run."""
    st.markdown(f"<style>{_CSS}</style>", unsafe_allow_html=True)


# ==================================================
# HELPER
# ==================================================

def esc(value):
    """Escape teks supaya aman dimasukkan ke HTML."""
    return html.escape(str(value if value is not None else ""))


def html_block(markup):
    """
    Render HTML lewat st.markdown. Indentasi dan baris kosong dibuang
    agar tidak dianggap sebagai blok kode oleh markdown.
    """
    flat = "".join(line.strip() for line in markup.splitlines())
    st.markdown(flat, unsafe_allow_html=True)


def to_list(value):
    """Ubah nilai skills (list / JSON / teks koma) menjadi list string."""
    if value is None:
        return []

    if isinstance(value, (list, tuple)):
        return [str(v).strip() for v in value if str(v).strip()]

    text = str(value).strip()

    if not text or text.lower() in ("nan", "none", "null"):
        return []

    if text.startswith("["):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [str(v).strip() for v in parsed if str(v).strip()]
        except (ValueError, TypeError):
            pass

    return [part.strip() for part in text.strip("[]").split(",") if part.strip()]


def text_to_html(text):
    """Teks biasa -> HTML aman dengan baris baru dipertahankan."""
    return esc(text).replace("\r\n", "\n").replace("\n", "<br>")


def logo():
    return (
        "<div class='jf-logo'><span class='jf-logo-mark'>J</span>"
        "<span>Jobify</span></div>"
    )


def page_header(title, accent, subtitle, badge=None):
    """Judul halaman: `title` biasa + `accent` berwarna teal."""
    badge_html = f"<span class='jf-badge'>{esc(badge)}</span>" if badge else ""

    html_block(
        f"""
        <div class="jf-page-head">
            {badge_html}
            <h1>{esc(title)} <span class="acc">{esc(accent)}</span></h1>
            <p>{esc(subtitle)}</p>
        </div>
        """
    )


def section_title(text):
    html_block(f"<div class='jf-section-title'>{esc(text)}</div>")


def stat_cards(items):
    """items: list of (label, value, caption, tone)."""
    cards = "".join(
        f"""
        <div class="jf-statcard jf-tone-{tone}">
            <small>{esc(label)}</small>
            <div class="v">{esc(value)}</div>
            <div class="c">{esc(caption)}</div>
        </div>
        """
        for label, value, caption, tone in items
    )
    html_block(f"<div class='jf-stat-grid'>{cards}</div>")


def chip(text, tone=""):
    cls = f"jf-chip jf-chip-{tone}" if tone else "jf-chip"
    return f"<span class='{cls}'>{esc(text)}</span>"


def chips(items, tone=""):
    """Baris chip. items: list teks atau list (teks, tone)."""
    parts = []

    for item in items:
        if isinstance(item, tuple):
            parts.append(chip(item[0], item[1]))
        else:
            parts.append(chip(item, tone))

    return f"<div class='jf-chips'>{''.join(parts)}</div>"


_LOGO_TONES = [
    ("#E8F7F2", "#0E8A6E"),
    ("#FFF0F0", "#D64545"),
    ("#EFEBFA", "#7C5CBF"),
    ("#FFF5E6", "#B86E00"),
]


def company_logo(name):
    """Kotak inisial perusahaan dengan warna konsisten per nama."""
    name = (name or "?").strip() or "?"
    bg, fg = _LOGO_TONES[sum(map(ord, name)) % len(_LOGO_TONES)]

    return (
        f"<div class='jf-job-logo' style='background:{bg};color:{fg}'>"
        f"{esc(name[0].upper())}</div>"
    )


def score_ring(score):
    """Lingkaran skor (0-100) dengan warna sesuai tingkat kecocokan."""
    try:
        score = max(0.0, min(float(score), 100.0))
    except (TypeError, ValueError):
        score = 0.0

    color = (
        "var(--jf-teal)" if score >= 75
        else "#F2A21B" if score >= 50
        else "var(--jf-coral)"
    )

    return (
        f"<div class='jf-ring' style='--p:{score:.0f};--c:{color}'>"
        f"<b>{score:.0f}%</b></div>"
    )


def meter(label, value, color="var(--jf-teal)"):
    """Bar horizontal untuk satu skor (0-100)."""
    try:
        value = max(0.0, min(float(value), 100.0))
    except (TypeError, ValueError):
        value = 0.0

    return (
        f"<div class='jf-meter'><div class='row'><span>{esc(label)}</span>"
        f"<span>{value:.2f}%</span></div>"
        f"<div class='track'><div class='fill' "
        f"style='width:{value:.1f}%;background:{color}'></div></div></div>"
    )


def details(summary, body_text):
    """Blok lipat berbasis <details> (aman dipakai di dalam expander)."""
    return (
        f"<details class='jf-details'><summary>{esc(summary)}</summary>"
        f"<div>{text_to_html(body_text)}</div></details>"
    )
