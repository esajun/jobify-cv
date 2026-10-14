
import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Membaca .env dari folder yang sama dengan database.py
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_PUBLISHABLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        f"Konfigurasi Supabase belum lengkap. "
        f"Periksa file: {env_path}"
    )

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
