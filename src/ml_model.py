"""
ml_model.py
------------
Menjembatani artefak hasil training (`scripts/train_model.py`) dengan
aplikasi Streamlit. Menyediakan dua fungsi utama:

1. predict_match_score(cv_text, cv_skills, job_text, job_skills)
   -> skor 0-100 untuk fitur "CV Screening" (1 CV vs 1 job description).

2. recommend_jobs(cv_text, cv_skills, top_n)
   -> daftar lowongan paling cocok dari data/jobs_processed.csv untuk
      fitur "Career Match" (1 CV vs seluruh katalog lowongan).

Jika artefak model belum ada (belum menjalankan scripts/train_model.py),
modul ini otomatis fallback ke pendekatan sederhana (TF-IDF on-the-fly),
supaya aplikasi tetap bisa jalan.
"""

import json
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "jobs_processed.csv")

_vectorizer = None
_classifier = None
_jobs_df = None
_jobs_tfidf_matrix = None  # precomputed TF-IDF matrix untuk seluruh katalog
_model_loaded = False


def _load_artifacts():
    """Load model, vectorizer, dan katalog lowongan sekali saja (cache di memori)."""
    global _vectorizer, _classifier, _jobs_df, _jobs_tfidf_matrix, _model_loaded

    if _model_loaded:
        return

    vec_path = os.path.join(MODEL_DIR, "tfidf_vectorizer.joblib")
    clf_path = os.path.join(MODEL_DIR, "match_classifier.joblib")

    if os.path.exists(vec_path) and os.path.exists(clf_path):
        _vectorizer = joblib.load(vec_path)
        _classifier = joblib.load(clf_path)

    if os.path.exists(DATA_PATH):
        _jobs_df = pd.read_csv(DATA_PATH)
        _jobs_df["skills_parsed"] = _jobs_df["skills"].apply(_parse_skill_list)

        # Precompute TF-IDF matrix seluruh katalog sekali saja, supaya
        # recommend_jobs() tidak perlu transform ulang per baris (jauh lebih cepat).
        if _vectorizer is not None:
            _jobs_tfidf_matrix = _vectorizer.transform(_jobs_df["job_text"].fillna("").tolist())

    _model_loaded = True


def _parse_skill_list(raw) -> list:
    if isinstance(raw, list):
        return raw
    if pd.isna(raw):
        return []
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [s.lower().strip() for s in parsed]
    except (json.JSONDecodeError, TypeError):
        pass
    return [s.strip().lower() for s in str(raw).split(",") if s.strip()]


def is_model_available() -> bool:
    _load_artifacts()
    return _vectorizer is not None and _classifier is not None


def is_catalog_available() -> bool:
    _load_artifacts()
    return _jobs_df is not None


def _tfidf_similarity(text_a: str, text_b: str) -> float:
    """Hitung cosine similarity. Pakai vectorizer terlatih kalau ada, kalau tidak fit on-the-fly."""
    _load_artifacts()

    if _vectorizer is not None:
        vecs = _vectorizer.transform([text_a, text_b])
    else:
        fallback_vectorizer = TfidfVectorizer(stop_words="english")
        vecs = fallback_vectorizer.fit_transform([text_a, text_b])

    return float(cosine_similarity(vecs[0:1], vecs[1:2])[0][0])


def _skill_overlap_ratio(candidate_skills: set, job_skills: set) -> float:
    if not job_skills:
        return 0.0
    return len(candidate_skills & job_skills) / len(job_skills)


def predict_match_score(cv_text: str, cv_skills: list, job_text: str, job_skills: list) -> dict:
    """
    Menghitung skor kecocokan CV terhadap satu job description, memakai model
    Logistic Regression terlatih (kalau tersedia), fallback ke rata-rata sederhana.

    Returns:
        dict dengan keys: final_score, skill_overlap_ratio, semantic_similarity, used_ml_model
    """
    _load_artifacts()

    cand_set = set(s.lower().strip() for s in cv_skills)
    job_set = set(s.lower().strip() for s in job_skills)

    overlap = _skill_overlap_ratio(cand_set, job_set)
    similarity = _tfidf_similarity(cv_text, job_text)

    if _classifier is not None:
        features = np.array([[overlap, similarity]])
        proba = _classifier.predict_proba(features)[0][1]
        final_score = round(float(proba) * 100, 2)
        used_ml_model = True
    else:
        # fallback: rata-rata berbobot manual (60% skill overlap, 40% semantic)
        final_score = round((overlap * 0.6 + similarity * 0.4) * 100, 2)
        used_ml_model = False

    return {
        "final_score": final_score,
        "skill_overlap_ratio": round(overlap * 100, 2),
        "semantic_similarity": round(similarity * 100, 2),
        "used_ml_model": used_ml_model,
    }


def recommend_jobs(cv_text: str, cv_skills: list, top_n: int = 5) -> pd.DataFrame:
    """
    Meranking seluruh lowongan di katalog (data/jobs_processed.csv) berdasarkan
    kecocokan dengan CV, memakai model yang sama dengan CV Screening.

    Returns:
        DataFrame kolom: job_title, company, role_family, match_score,
        matched_skills, missing_skills — diurutkan dari skor tertinggi.
    """
    _load_artifacts()

    if _jobs_df is None:
        raise FileNotFoundError(
            "Katalog lowongan (data/jobs_processed.csv) tidak ditemukan. "
            "Pastikan file tersedia di folder data/."
        )

    cand_set = set(s.lower().strip() for s in cv_skills)

    # --- Skill overlap ratio (vectorized, murah karena cuma operasi set) ---
    overlaps = np.array([
        _skill_overlap_ratio(cand_set, set(skills)) for skills in _jobs_df["skills_parsed"]
    ])

    # --- Semantic similarity: transform CV sekali, lalu cosine similarity ke SEMUA
    #     lowongan sekaligus (operasi matriks, bukan loop) ---
    if _vectorizer is not None and _jobs_tfidf_matrix is not None:
        cv_vector = _vectorizer.transform([cv_text])
        similarities = cosine_similarity(cv_vector, _jobs_tfidf_matrix)[0]
    else:
        fallback_vectorizer = TfidfVectorizer(stop_words="english")
        corpus = [cv_text] + _jobs_df["job_text"].fillna("").tolist()
        matrix = fallback_vectorizer.fit_transform(corpus)
        similarities = cosine_similarity(matrix[0:1], matrix[1:])[0]

    # --- Skor akhir (vectorized) ---
    if _classifier is not None:
        features = np.column_stack([overlaps, similarities])
        scores = _classifier.predict_proba(features)[:, 1] * 100
    else:
        scores = (overlaps * 0.6 + similarities * 0.4) * 100

    display_cols = ["job_title", "company", "role_family", "location", "salary", "job_type", "education", "experience", "job_links", "description", "requirements"]
    display_cols = [c for c in display_cols if c in _jobs_df.columns]
    result_df = _jobs_df[display_cols].copy()
    result_df["match_score"] = np.round(scores, 2)
    result_df["matched_skills"] = [
        sorted(cand_set & set(skills)) for skills in _jobs_df["skills_parsed"]
    ]
    result_df["missing_skills"] = [
        sorted(set(skills) - cand_set) for skills in _jobs_df["skills_parsed"]
    ]

    result_df = result_df.sort_values("match_score", ascending=False)
    return result_df.head(top_n).reset_index(drop=True)
