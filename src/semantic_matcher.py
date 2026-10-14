"""
semantic_matcher.py
--------------------
Menghitung skor kemiripan semantik antara dua teks (CV vs job description).

Kalau `models/tfidf_vectorizer.joblib` sudah ada (hasil `scripts/train_model.py`,
di-fit dari ribuan job_text di data/jobs_processed.csv), vectorizer itu yang
dipakai -- hasilnya lebih representatif karena "kosakata"-nya belajar dari
data lowongan asli, bukan cuma dari 2 teks yang sedang dibandingkan.

Kalau belum ada (belum training), fallback ke TF-IDF yang di-fit on-the-fly
dari 2 teks yang dibandingkan saja (versi awal, tetap jalan tanpa training).
"""

import os

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
VECTORIZER_PATH = os.path.join(MODEL_DIR, "tfidf_vectorizer.joblib")

_vectorizer_cache = None
_vectorizer_loaded = False


def _load_trained_vectorizer():
    global _vectorizer_cache, _vectorizer_loaded

    if _vectorizer_loaded:
        return _vectorizer_cache

    if os.path.exists(VECTORIZER_PATH):
        _vectorizer_cache = joblib.load(VECTORIZER_PATH)

    _vectorizer_loaded = True
    return _vectorizer_cache


def using_trained_vectorizer() -> bool:
    return _load_trained_vectorizer() is not None


def calculate_semantic_similarity(text_a: str, text_b: str) -> float:
    """
    Menghitung skor kemiripan semantik antara dua teks dalam skala 0-100.

    Args:
        text_a: teks pertama (mis. isi CV).
        text_b: teks kedua (mis. job description).

    Returns:
        Skor kemiripan (float, 0-100). Mengembalikan 0 jika salah satu teks kosong.
    """
    text_a = (text_a or "").strip()
    text_b = (text_b or "").strip()

    if not text_a or not text_b:
        return 0.0

    vectorizer = _load_trained_vectorizer()

    if vectorizer is not None:
        tfidf_matrix = vectorizer.transform([text_a, text_b])
    else:
        fallback_vectorizer = TfidfVectorizer(stop_words="english")
        tfidf_matrix = fallback_vectorizer.fit_transform([text_a, text_b])

    similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]

    return float(similarity) * 100
