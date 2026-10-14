
import os
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(Path(__file__).resolve().parent / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_PUBLISHABLE_KEY")
RESET_REDIRECT_URL = os.getenv("PASSWORD_RESET_REDIRECT_URL")


def _new_client():
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("Konfigurasi Supabase belum lengkap.")

    return create_client(SUPABASE_URL, SUPABASE_KEY)


def get_client():
    user = st.session_state.get("user")

    if not user:
        raise RuntimeError("Pengguna belum login.")

    client = _new_client()
    client.auth.set_session(
        user["access_token"],
        user["refresh_token"],
    )
    return client


def login(email, password):
    client = _new_client()

    response = client.auth.sign_in_with_password({
        "email": email,
        "password": password,
    })

    if not response.user or not response.session:
        raise RuntimeError("Login gagal.")

    profile_response = (
        client.table("profiles")
        .select("full_name, role")
        .eq("id", response.user.id)
        .execute()
    )

    profile = (
        profile_response.data[0]
        if profile_response.data
        else {}
    )

    role = profile.get("role", "user")

    if role not in ("admin", "user"):
        role = "user"

    st.session_state["user"] = {
        "id": response.user.id,
        "email": response.user.email,
        "full_name": (
            profile.get("full_name")
            or (response.user.user_metadata or {}).get("full_name")
            or response.user.email
        ),
        "role": role,
        "access_token": response.session.access_token,
        "refresh_token": response.session.refresh_token,
    }


def register(full_name, email, password):
    client = _new_client()

    response = client.auth.sign_up({
        "email": email,
        "password": password,
        "options": {
            "data": {"full_name": full_name}
        },
    })

    if not response.user or not response.session:
        return False

    profile = (
        client.table("profiles")
        .select("id")
        .eq("id", response.user.id)
        .execute()
    )

    if not profile.data:
        client.table("profiles").insert({
            "id": response.user.id,
            "full_name": full_name,
            "role": "user",
        }).execute()

    return True


def send_password_reset(email):
    if not RESET_REDIRECT_URL:
        raise RuntimeError(
            "PASSWORD_RESET_REDIRECT_URL belum dikonfigurasi."
        )

    client = _new_client()
    client.auth.reset_password_for_email(
        email,
        options={"redirect_to": RESET_REDIRECT_URL},
    )




def exchange_recovery_link(code=None, token_hash=None):
    client = _new_client()

    if code:
        response = client.auth.exchange_code_for_session(code)

    elif token_hash:
        response = client.auth.verify_otp({
            "token_hash": token_hash,
            "type": "recovery",
        })

    else:
        raise RuntimeError("Kode pemulihan tidak ditemukan.")

    if not response.session:
        raise RuntimeError(
            "Sesi pemulihan gagal dibuat. Minta link reset baru."
        )

    return {
        "access_token": response.session.access_token,
        "refresh_token": response.session.refresh_token,
    }



def update_password(access_token, refresh_token, new_password):
    client = _new_client()
    client.auth.set_session(access_token, refresh_token)
    client.auth.update_user({"password": new_password})


def logout():
    try:
        if st.session_state.get("user"):
            get_client().auth.sign_out()
    finally:
        st.session_state.pop("user", None)
        st.session_state.pop("role", None)
