"""Halaman Profil: data akun, riwayat CV Screening, dan riwayat Career Match."""

import streamlit as st

from auth import get_client
from ui import esc, html_block, page_header, section_title

HISTORY_PAGE_SIZE = 10


def _fetch_history(table, user_id, page):
    """Ambil satu halaman riwayat milik user. Return (rows, total)."""
    start = (page - 1) * HISTORY_PAGE_SIZE
    end = start + HISTORY_PAGE_SIZE - 1

    response = (
        get_client()
        .table(table)
        .select("*", count="exact")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .range(start, end)
        .execute()
    )

    rows = response.data or []
    total = response.count if response.count is not None else len(rows)
    return rows, total


def _pager(state_key, page, total_pages):
    """Tombol Sebelumnya / Berikutnya untuk satu daftar riwayat."""
    if total_pages <= 1:
        return

    prev_col, page_col, next_col = st.columns([1, 2, 1])

    with prev_col:
        if st.button(
            "← Sebelumnya",
            disabled=page <= 1,
            use_container_width=True,
            key=f"prev_{state_key}",
        ):
            st.session_state[state_key] = page - 1
            st.rerun()

    with page_col:
        st.markdown(
            f"<div class='jf-pager'>Halaman <b>{page}</b> dari "
            f"<b>{total_pages}</b></div>",
            unsafe_allow_html=True,
        )

    with next_col:
        if st.button(
            "Berikutnya →",
            disabled=page >= total_pages,
            use_container_width=True,
            key=f"next_{state_key}",
        ):
            st.session_state[state_key] = page + 1
            st.rerun()


def _render_history(table, user_id, state_key, render_item, empty_message):
    page = max(1, st.session_state.get(state_key, 1))

    try:
        rows, total = _fetch_history(table, user_id, page)

        total_pages = max(
            1, (total + HISTORY_PAGE_SIZE - 1) // HISTORY_PAGE_SIZE
        )

        # Halaman melebihi batas (mis. data terhapus): kembali ke halaman akhir
        if page > total_pages:
            page = total_pages
            st.session_state[state_key] = page
            rows, total = _fetch_history(table, user_id, page)

    except Exception:
        st.warning(
            "Riwayat belum dapat ditampilkan. "
            "Coba muat ulang halaman beberapa saat lagi."
        )
        return 0

    if not rows:
        st.info(empty_message)
        return total

    offset = (page - 1) * HISTORY_PAGE_SIZE

    for index, item in enumerate(rows):
        # index unik per halaman supaya key widget tidak bentrok
        render_item(item, offset + index)

    _pager(state_key, page, total_pages)
    return total


def run_profile():
    user = st.session_state.get("user", {})
    user_id = user.get("id")

    name = user.get("full_name") or "Pengguna"
    email = user.get("email") or "-"
    initial = name.strip()[:1].upper() or "U"

    page_header(
        "Profil",
        "Saya",
        "Lihat data akun dan seluruh riwayat analisis CV serta "
        "rekomendasi lowonganmu.",
        badge="Akun",
    )

    # ==========================================
    # DATA AKUN
    # ==========================================
    # Streamlit memberi margin bawah negatif pada blok markdown sehingga
    # isi kartu terlihat turun. Di kartu profil margin itu dinolkan.
    st.markdown(
        "<style>"
        ".st-key-card_profile [data-testid='stMarkdownContainer'],"
        ".st-key-card_profile [data-testid='stMarkdownContainer'] > *,"
        ".st-key-card_profile [data-testid='stElementContainer']"
        "{margin:0 !important;}"
        "</style>",
        unsafe_allow_html=True,
    )

    with st.container(border=True, key="card_profile"):
        html_block(
            f"""
            <div style="display:flex;align-items:center;gap:20px;flex-wrap:wrap;padding:4px">
                <div style="flex:none;width:76px;height:76px;border-radius:50%;background:var(--jf-teal);color:#fff;display:grid;place-items:center;font-size:2rem;font-weight:700">{esc(initial)}</div>
                <div style="display:flex;flex-direction:column;gap:6px;min-width:0">
                    <div style="font-size:1.35rem;font-weight:700;line-height:1.2;color:var(--jf-ink)">{esc(name)}</div>
                    <div style="font-size:0.95rem;color:var(--jf-muted);overflow-wrap:anywhere">{esc(email)}</div>
                    <div><span class="jf-role-pill">Pencari Kerja</span></div>
                </div>
            </div>
            """
        )

    if not user_id:
        st.info("Login terlebih dahulu untuk melihat riwayat.")
        return

    # Import di dalam fungsi agar halaman lain tidak ikut termuat
    from pages.cv_screening import display_history_item as cv_item
    from pages.career_match import display_history_item as match_item

    # ==========================================
    # RIWAYAT CV SCREENING
    # ==========================================
    section_title("Riwayat CV Screening")
    st.caption("Seluruh analisis CV yang pernah kamu lakukan.")

    _render_history(
        "cv_screening_history",
        user_id,
        "profile_cv_page",
        # key kartu dibedakan dari halaman aslinya
        lambda item, i: cv_item(item, f"profile_cv_{i}"),
        "Belum ada riwayat CV Screening. "
        "Hasil analisis berikutnya akan muncul di sini.",
    )

    # ==========================================
    # RIWAYAT CAREER MATCH
    # ==========================================
    section_title("Riwayat Career Match")
    st.caption("Seluruh rekomendasi lowongan dari CV yang pernah kamu upload.")

    _render_history(
        "career_match_history",
        user_id,
        "profile_match_page",
        lambda item, i: match_item(item, f"profile_match_{i}"),
        "Belum ada riwayat Career Match. "
        "Hasil pencarian berikutnya akan muncul di sini.",
    )
