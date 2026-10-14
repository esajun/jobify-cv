import streamlit as st

from auth import login, register, logout, get_client

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
    </style>
    """,
    unsafe_allow_html=True,
)

# Login dan register
if "user" not in st.session_state:
    st.title("Jobify")
    st.write("Masuk untuk menemukan lowongan yang sesuai dengan kariermu.")

    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input(
                "Password", type="password", key="login_password"
            )
            submitted = st.form_submit_button("Login", type="primary")

        if submitted:
            try:
                login(email.strip(), password)
                st.rerun()
            except Exception:
                st.error(
                    "Login gagal. Periksa email, password, dan profil akun."
                )

    
    with tab_register:
        with st.form("register_form"):
            full_name = st.text_input("Nama lengkap")
            email = st.text_input("Email", key="register_email")
            password = st.text_input(
                "Password (minimal 6 karakter)",
                type="password",
                key="register_password",
            )
            confirm_password = st.text_input(
                "Konfirmasi password",
                type="password",
            )
            submitted = st.form_submit_button(
                "Buat Akun", type="primary"
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
                        full_name.strip(), email.strip(), password
                    )

                    if has_session:
                        login(email.strip(), password)
                        st.success("Registrasi berhasil! Kamu sudah login.")
                        st.rerun()
                    else:
                        st.error(
                            "Sesi login belum tersedia. Periksa pengaturan "
                            "Confirm email di Supabase dan fungsi register() "
                            "di auth.py."
                        )

                except Exception as e:
                    st.error(f"Registrasi gagal: {e}")

    st.stop()


# Routing berdasarkan role
user = st.session_state["user"]

# Navbar untuk Admin dan User
if user["role"] == "admin":
    nav1, nav2, nav3 = st.columns([3, 2, 1])

    with nav1:
        st.markdown("## 💼 Jobify")
    with nav2:
        st.markdown("**Admin Dashboard**")
    with nav3:
        if st.button("Logout", use_container_width=True, key="admin_logout"):
            logout()
            st.rerun()

    st.divider()

    from pages.admin_dashboard import run_admin_dashboard
    run_admin_dashboard(get_client())

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
        if st.button("Logout", use_container_width=True, key="user_logout"):
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
