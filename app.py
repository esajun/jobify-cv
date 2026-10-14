
import streamlit as st

from auth import (
    login,
    register,
    logout,
    get_client,
    send_password_reset,
    exchange_recovery_link,
    update_password,
)

st.set_page_config(
    page_title="Jobify - Career Match",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }

        [data-testid="stSidebar"] {
            display: none;
        }

        [data-testid="collapsedControl"] {
            display: none;
        }

        .forgot-password {
            text-align: right;
            margin-top: -8px;
            margin-bottom: 12px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)



# ==================================================
# PEMROSESAN LINK RESET PASSWORD DARI SUPABASE
# ==================================================

import json
import streamlit.components.v1 as components

# Membaca token dari URL fragment (#...)
fragment_data = components.html(
    """
    <script>
    const hash = window.parent.location.hash;

    if (hash && hash.includes("type=recovery")) {
        const params = new URLSearchParams(hash.substring(1));

        const data = {
            access_token: params.get("access_token"),
            refresh_token: params.get("refresh_token"),
            type: params.get("type")
        };

        window.parent.postMessage({
            isJobifyRecovery: true,
            payload: data
        }, window.location.origin);
    }
    </script>
    """,
    height=0,
)

# Parameter code/token_hash tetap diperiksa seperti sebelumnya
recovery_code = st.query_params.get("code")
recovery_token_hash = st.query_params.get("token_hash")
recovery_type = st.query_params.get("type")

if (
    recovery_code
    or (recovery_token_hash and recovery_type == "recovery")
) and "reset_access_token" not in st.session_state:
    try:
        recovery = exchange_recovery_link(
            code=recovery_code,
            token_hash=recovery_token_hash,
        )

        st.session_state["reset_access_token"] = recovery["access_token"]
        st.session_state["reset_refresh_token"] = recovery["refresh_token"]

        st.query_params.clear()
        st.rerun()

    except Exception:
        st.error(
            "Link reset tidak valid atau sudah kedaluwarsa. "
            "Silakan minta link reset password yang baru."
        )
        st.stop()


# ==================================================
# HALAMAN PASSWORD BARU
# ==================================================

if "reset_access_token" in st.session_state:
    st.title("🔐 Buat Password Baru")
    st.write("Masukkan password baru untuk akun Jobify kamu.")

    with st.form("new_password_form"):
        new_password = st.text_input(
            "Password Baru",
            type="password",
        )
        confirm_password = st.text_input(
            "Konfirmasi Password Baru",
            type="password",
        )

        submitted = st.form_submit_button(
            "Simpan Password",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if len(new_password) < 6:
            st.error("Password minimal 6 karakter.")
        elif new_password != confirm_password:
            st.error("Konfirmasi password tidak sama.")
        else:
            try:
                update_password(
                    st.session_state["reset_access_token"],
                    st.session_state["reset_refresh_token"],
                    new_password,
                )

                st.session_state.pop("reset_access_token", None)
                st.session_state.pop("reset_refresh_token", None)
                st.session_state["password_reset_success"] = True
                st.rerun()

            except Exception:
                st.error(
                    "Password gagal diperbarui. "
                    "Silakan minta link reset yang baru."
                )

    st.stop()


# ==================================================
# KONFIRMASI RESET BERHASIL
# ==================================================

if st.session_state.get("password_reset_success"):
    st.title("🔐 Password Berhasil Diubah")
    st.success(
        "Password kamu sudah diperbarui. "
        "Silakan login menggunakan password baru."
    )

    if st.button("Kembali ke Login", type="primary"):
        st.session_state.pop("password_reset_success", None)
        st.rerun()

    st.stop()


# ==================================================
# LOGIN, LUPA PASSWORD, DAN REGISTER
# ==================================================

if "user" not in st.session_state:
    st.title("💼 Jobify")
    st.write(
        "Masuk untuk menemukan lowongan yang sesuai dengan kariermu."
    )

    tab_login, tab_register = st.tabs(["Login", "Register"])

    # --------------------------------------------------
    # LOGIN
    # --------------------------------------------------

    with tab_login:
        with st.form("login_form"):
            email = st.text_input(
                "Email",
                key="login_email",
            )

            password = st.text_input(
                "Password",
                type="password",
                key="login_password",
            )

            # Tombol login diproses di bawah form.
            submitted = st.form_submit_button(
                "Login",
                type="primary",
                use_container_width=True,
            )

        # Link bantuan diletakkan tepat di atas tombol Login
        # secara visual melalui area sebelum form login.
        with st.expander("Lupa Password?"):
            st.write(
                "Masukkan email akun Jobify untuk menerima "
                "link pembuatan password baru."
            )

            with st.form("forgot_password_form"):
                reset_email = st.text_input(
                    "Email akun",
                    key="reset_email",
                    placeholder="nama@email.com",
                )

                reset_submitted = st.form_submit_button(
                    "Kirim Link Reset",
                    use_container_width=True,
                )

            if reset_submitted:
                if not reset_email.strip():
                    st.error("Email wajib diisi.")
                else:
                    try:
                        send_password_reset(reset_email.strip())
                        st.success(
                            "Jika email terdaftar, link reset "
                            "akan dikirim. Periksa inbox dan spam."
                        )
                    except Exception:
                        st.error(
                            "Link reset gagal dikirim. "
                            "Periksa konfigurasi Supabase dan email."
                        )

        if submitted:
            if not email.strip() or not password:
                st.error("Email dan password wajib diisi.")
            else:
                try:
                    login(email.strip(), password)
                    st.rerun()
                except Exception:
                    st.error(
                        "Login gagal. Periksa email, password, "
                        "dan profil akun."
                    )

    # --------------------------------------------------
    # REGISTER
    # --------------------------------------------------

    with tab_register:
        with st.form("register_form"):
            full_name = st.text_input(
                "Nama lengkap",
                key="register_full_name",
            )

            email = st.text_input(
                "Email",
                key="register_email",
            )

            password = st.text_input(
                "Password (minimal 6 karakter)",
                type="password",
                key="register_password",
            )

            confirm_password = st.text_input(
                "Konfirmasi password",
                type="password",
                key="register_confirm_password",
            )

            submitted = st.form_submit_button(
                "Buat Akun",
                type="primary",
                use_container_width=True,
            )

        if submitted:
            if not full_name.strip() or not email.strip():
                st.error("Nama dan email wajib diisi.")
            elif len(password) < 6:
                st.error("Password minimal 6 karakter.")
            elif password != confirm_password:
                st.error("Konfirmasi password tidak sama.")
            else:
                try:
                    has_session = register(
                        full_name.strip(),
                        email.strip(),
                        password,
                    )

                    if has_session:
                        login(email.strip(), password)
                        st.success(
                            "Registrasi berhasil! Kamu sudah login."
                        )
                        st.rerun()
                    else:
                        st.error(
                            "Sesi login belum tersedia. Periksa "
                            "pengaturan Confirm email di Supabase."
                        )
                except Exception:
                    st.error(
                        "Registrasi gagal. Email mungkin sudah "
                        "terdaftar atau ada masalah konfigurasi."
                    )

    st.stop()


# ==================================================
# ROUTING BERDASARKAN ROLE
# ==================================================

user = st.session_state["user"]


# ==================================================
# DASHBOARD ADMIN
# ==================================================

if user["role"] == "admin":
    nav1, nav2, nav3 = st.columns([3, 2, 1])

    with nav1:
        st.markdown("## 💼 Jobify")

    with nav2:
        st.markdown("**Admin Dashboard**")

    with nav3:
        if st.button(
            "Logout",
            use_container_width=True,
            key="admin_logout",
        ):
            logout()
            st.rerun()

    st.divider()

    from pages.admin_dashboard import run_admin_dashboard

    run_admin_dashboard(get_client())


# ==================================================
# DASHBOARD USER
# ==================================================

else:
    if "user_page" not in st.session_state:
        st.session_state["user_page"] = "dashboard"

    nav1, nav2, nav3, nav4, nav5 = st.columns([2, 2, 2, 2, 1])

    with nav1:
        st.markdown("## 💼 Jobify")

    with nav2:
        if st.button("🏠 Dashboard", use_container_width=True):
            st.session_state["user_page"] = "dashboard"
            st.rerun()

    with nav3:
        if st.button("🔍 CV Screening", use_container_width=True):
            st.session_state["user_page"] = "screening"
            st.rerun()

    with nav4:
        if st.button("🎯 Career Match", use_container_width=True):
            st.session_state["user_page"] = "career_match"
            st.rerun()

    with nav5:
        if st.button(
            "Logout",
            use_container_width=True,
            key="user_logout",
        ):
            logout()
            st.rerun()

    st.divider()

    current_page = st.session_state["user_page"]

    if current_page == "dashboard":
        from pages.user_dashboard import run_user_dashboard
        run_user_dashboard()

    elif current_page == "screening":
        from pages.cv_screening import run_cv_screening
        run_cv_screening()

    elif current_page == "career_match":
        from pages.career_match import run_career_match
        run_career_match()
