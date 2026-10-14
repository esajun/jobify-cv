"""
skill_extractor.py
-------------------
Mengekstrak skill/kata kunci dari teks CV maupun job description.

Prioritas sumber daftar skill:
1. `models/skill_vocab.json` — dihasilkan oleh `scripts/train_model.py` dari
   kolom `skills` di `data/jobs_processed.csv` (data asli, ribuan skill unik).
2. Jika file itu belum ada (belum pernah training), fallback ke daftar manual
   kecil (`FALLBACK_SKILL_KEYWORDS`) supaya aplikasi tetap bisa dipakai.
"""

import json
import os
import re

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
SKILL_VOCAB_PATH = os.path.join(MODEL_DIR, "skill_vocab.json")

# Dipakai HANYA kalau skill_vocab.json belum tersedia (belum training).
FALLBACK_SKILL_KEYWORDS = [
    "python", "java", "javascript", "sql", "excel", "power bi", "tableau",
    "machine learning", "data analysis", "komunikasi", "leadership",
    "project management", "digital marketing", "figma", "git",
]

_skill_vocab_cache = None


def _load_skill_vocab() -> list:
    global _skill_vocab_cache

    if _skill_vocab_cache is not None:
        return _skill_vocab_cache

    if os.path.exists(SKILL_VOCAB_PATH):
        with open(SKILL_VOCAB_PATH, "r", encoding="utf-8") as f:
            _skill_vocab_cache = json.load(f)
    else:
        _skill_vocab_cache = FALLBACK_SKILL_KEYWORDS

    return _skill_vocab_cache


def extract_key_phrases(text: str) -> list:
    """
    Mengekstrak daftar frasa/skill unik dari sebuah teks, dengan mencocokkan
    ke skill vocabulary (dari data asli, atau fallback manual).

    Args:
        text: teks mentah (CV atau job description).

    Returns:
        List string berisi skill/frasa kunci (lowercase, tanpa duplikat, terurut).
    """
    if not text or not text.strip():
        return []

    text_lower = text.lower()
    vocab = _load_skill_vocab()
    found = set()

    for skill in vocab:
        skill = skill.strip()
        if not skill:
            continue
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text_lower):
            found.add(skill)

    return sorted(found)


def skill_vocab_size() -> int:
    """Info kecil untuk ditampilkan di UI: berapa banyak skill yang dikenali sistem."""
    return len(_load_skill_vocab())


def using_trained_vocab() -> bool:
    """True kalau skill_vocab.json (hasil training dari data asli) tersedia."""
    return os.path.exists(SKILL_VOCAB_PATH)
