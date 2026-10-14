
import os
import json
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

BASE_DIR = Path(__file__).resolve().parent
env_path = BASE_DIR / ".env"
load_dotenv(env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

if not SUPABASE_URL or not SUPABASE_SECRET_KEY:
    raise ValueError("Konfigurasi Supabase untuk impor belum lengkap.")

supabase = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)

FILE_PATH = BASE_DIR / "data" / "jobs_processed.csv"
BATCH_SIZE = 100

if not FILE_PATH.exists():
    raise FileNotFoundError(f"Dataset tidak ditemukan: {FILE_PATH}")

df = pd.read_csv(FILE_PATH)

print(f"Total data CSV: {len(df)}")

# Mapping dataset hasil preprocessing ke kolom Supabase.
column_mapping = {
    "job_title": "title",
    "company": "company",
    "location": "location",
    "job_type": "job_type",
    "salary": "salary",
    "education_required": "education",
    "experience": "experience",
    "description": "description",
    "skills_joined": "skills",
    "job_links": "job_url",
    "requirements": "requirements",
    "job_benefits": "benefits",
}

df = df[list(column_mapping.keys())].rename(columns=column_mapping)

# Pastikan URL tersedia dan tidak kosong.
df["job_url"] = df["job_url"].fillna("").astype(str).str.strip()
df = df[df["job_url"] != ""].drop_duplicates(
    subset=["job_url"], keep="first"
)

# Rapikan nilai kosong agar kompatibel dengan JSON.
df = df.astype(object).where(pd.notna(df), None)

# Skills disimpan sebagai teks gabungan agar cocok dengan dashboard lama.
records = df.to_dict(orient="records")

print(f"Data siap diimpor: {len(records)}")

# Upsert menghindari duplikasi berdasarkan job_url,
# jika job_url sudah diberi UNIQUE constraint di Supabase.
for start in range(0, len(records), BATCH_SIZE):
    batch = records[start:start + BATCH_SIZE]

    supabase.table("jobs").insert(batch).execute()

    print(f"Diproses: {min(start + len(batch), len(records))}/{len(records)}")

print("Upsert lowongan selesai!")
