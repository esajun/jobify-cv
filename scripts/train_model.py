"""
train_model.py
----------------
Melatih "otak" dari sistem Career Match & CV Screening, berdasarkan
data lowongan asli di `data/jobs_processed.csv`. Menghasilkan 3 artefak
yang disimpan ke folder `models/`:

1. skill_vocab.json
   Daftar skill unik yang diambil dari kolom `skills` seluruh lowongan.
   Dipakai `src/skill_extractor.py` supaya daftar skill jauh lebih kaya
   dibanding daftar manual, karena berasal dari data asli.

2. tfidf_vectorizer.joblib
   TF-IDF vectorizer yang di-fit dari `job_text` seluruh lowongan (bukan cuma
   1 CV vs 1 JD seperti versi awal). Dengan begini representasi kata jadi
   lebih representatif ("belajar" dari ribuan lowongan asli).

3. match_classifier.joblib
   Model Logistic Regression yang belajar memprediksi probabilitas
   "match" antara kandidat & lowongan, berdasarkan 2 fitur:
     - skill_overlap_ratio : proporsi skill lowongan yang dimiliki kandidat
     - tfidf_similarity     : kemiripan teks (TF-IDF cosine similarity)

   Karena kita tidak punya data CV asli berlabel match/tidak-match,
   label dibuat dengan WEAK SUPERVISION (mirip pendekatan notebook
   eksperimen tim AI Engineer kamu, tapi jauh lebih sederhana):
     - Pasangan POSITIF (label 1): sebuah lowongan dipasangkan dengan
       teks skill-nya sendiri -> representasi "kandidat ideal" untuk
       lowongan tsb.
     - Pasangan NEGATIF (label 0): sebuah lowongan dipasangkan dengan
       teks skill dari lowongan LAIN yang role_family-nya berbeda
       -> representasi kandidat yang kemungkinan besar tidak relevan.

   Model ini menggantikan pembobotan manual (60% requirement + 40% semantic)
   dengan bobot yang benar-benar dipelajari dari data.

Cara pakai:
    python scripts/train_model.py --data data/jobs_processed.csv --out_dir models
"""

import argparse
import ast
import json
import random

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report


def parse_skill_list(raw) -> list:
    """Parse kolom `skills` (bisa berbentuk string JSON list) jadi list Python."""
    if isinstance(raw, list):
        return raw
    if pd.isna(raw):
        return []
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return parsed
    except (json.JSONDecodeError, TypeError):
        pass
    try:
        parsed = ast.literal_eval(raw)
        if isinstance(parsed, list):
            return parsed
    except (ValueError, SyntaxError):
        pass
    # fallback: split by koma
    return [s.strip() for s in str(raw).split(",") if s.strip()]


# Beberapa entri di kolom `skills` sumber ternyata cuma kata umum/stopword
# (kemungkinan noise dari proses scraping), bukan skill sungguhan -> dibuang.
SKILL_STOPWORD_BLOCKLIST = {
    "dan", "atau", "dengan", "untuk", "yang", "dari", "pada", "dll", "dst",
    "menguasai", "memahami", "familiar", "familiar dengan", "berpengalaman",
    "data", "power", "kerja", "tim", "baik", "mampu", "bisa",
}


# Daftar skill umum yang dikurasi manual, digabung ke hasil mining dari data.
# Diperlukan karena kolom `skills_clean` di data mentah ternyata banyak yang
# "nyambung" tanpa pemisah antar skill (bug di sisi scraping/data asli, mis.
# "Power BIExtract, Transform, Load (ETL)Python" harusnya 3 skill terpisah).
# Akibatnya sejumlah skill umum seperti "power bi" jarang muncul BERDIRI SENDIRI
# di data mentah -- daftar ini memastikan skill-skill penting tetap dikenali.
CURATED_SEED_SKILLS = [
    "python", "java", "javascript", "typescript", "c++", "c#", "php", "golang", "sql",
    "html", "css", "react", "vue", "angular", "node.js", "django", "flask",
    "excel", "microsoft excel", "power bi", "tableau", "power query", "power automate",
    "machine learning", "deep learning", "data analysis", "data science", "data visualization",
    "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy", "etl", "big data",
    "aws", "azure", "google cloud", "docker", "kubernetes", "git", "github", "linux",
    "project management", "agile", "scrum", "digital marketing", "seo",
    "content writing", "copywriting", "business analysis", "product management",
    "ui/ux", "figma", "photoshop", "microsoft word", "microsoft powerpoint",
    "komunikasi", "kepemimpinan", "leadership", "teamwork", "problem solving",
    "manajemen waktu", "time management", "critical thinking", "public speaking",
]

# Token hasil mining dari data hanya dipakai kalau muncul minimal segini kali
# di seluruh dataset. Token yang cuma muncul 1x kemungkinan besar hasil
# "nyambung" (concatenation bug), bukan skill yang valid.
MIN_SKILL_FREQUENCY = 3


def build_skill_vocab(df: pd.DataFrame) -> list:
    from collections import Counter

    counts = Counter()
    for skills in df["skills_parsed"]:
        for s in skills:
            s_clean = s.strip().lower()
            if not s_clean or s_clean in SKILL_STOPWORD_BLOCKLIST:
                continue
            counts[s_clean] += 1

    mined = {s for s, c in counts.items() if c >= MIN_SKILL_FREQUENCY}
    vocab = mined | set(CURATED_SEED_SKILLS)
    return sorted(vocab)


def skill_overlap_ratio(candidate_skills: set, job_skills: set) -> float:
    if not job_skills:
        return 0.0
    return len(candidate_skills & job_skills) / len(job_skills)


def build_training_pairs(df: pd.DataFrame, n_negatives_per_job: int = 2, seed: int = 42):
    """Bangun pasangan (job, kandidat_sintetis, label) via weak supervision."""
    random.seed(seed)
    rows = df.to_dict("records")
    by_family = {}
    for r in rows:
        by_family.setdefault(r["role_family"], []).append(r)

    pairs = []
    for job in rows:
        job_skills = set(job["skills_parsed"])

        # --- Pasangan positif: kandidat "ideal" = skill lowongan itu sendiri
        pairs.append({
            "job_text": job["job_text"],
            "candidate_text": job["job_text"],
            "candidate_skills": job_skills,
            "job_skills": job_skills,
            "label": 1,
        })

        # --- Pasangan negatif: kandidat dari role_family lain
        other_families = [f for f in by_family if f != job["role_family"]]
        if not other_families:
            continue
        for _ in range(n_negatives_per_job):
            neg_family = random.choice(other_families)
            neg_job = random.choice(by_family[neg_family])
            neg_skills = set(neg_job["skills_parsed"])
            pairs.append({
                "job_text": job["job_text"],
                "candidate_text": neg_job["job_text"],
                "candidate_skills": neg_skills,
                "job_skills": job_skills,
                "label": 0,
            })

    return pd.DataFrame(pairs)


def main(data_path: str, out_dir: str):
    df = pd.read_csv(data_path)
    df = df.dropna(subset=["job_text", "skills_joined", "role_family"]).reset_index(drop=True)
    df["skills_parsed"] = df["skills"].apply(parse_skill_list)
    df["skills_parsed"] = df["skills_parsed"].apply(lambda lst: [s.lower().strip() for s in lst])

    print(f"Total lowongan dipakai untuk training: {len(df)}")

    # 1) Skill vocabulary
    skill_vocab = build_skill_vocab(df)
    print(f"Jumlah skill unik ditemukan: {len(skill_vocab)}")

    # 2) TF-IDF vectorizer, di-fit dari seluruh job_text
    vectorizer = TfidfVectorizer(max_features=5000, stop_words="english")
    vectorizer.fit(df["job_text"].tolist())

    # 3) Bangun training pairs (weak supervision)
    pairs_df = build_training_pairs(df, n_negatives_per_job=2)
    print(f"Total pasangan training (weak supervision): {len(pairs_df)}")

    # Hitung fitur: skill_overlap_ratio & tfidf_similarity
    job_vectors = vectorizer.transform(pairs_df["job_text"].tolist())
    cand_vectors = vectorizer.transform(pairs_df["candidate_text"].fillna("").tolist())

    tfidf_sims = np.array([
        cosine_similarity(job_vectors[i], cand_vectors[i])[0][0]
        for i in range(pairs_df.shape[0])
    ])

    overlap_ratios = np.array([
        skill_overlap_ratio(row.candidate_skills, row.job_skills)
        for row in pairs_df.itertuples()
    ])

    X = np.column_stack([overlap_ratios, tfidf_sims])
    y = pairs_df["label"].values

    # 4) Train/test split & training Logistic Regression
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    clf = LogisticRegression()
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    print("\n=== Classification Report (test set) ===")
    print(classification_report(y_test, y_pred, target_names=["not_match", "match"]))
    print("Koefisien model [skill_overlap_ratio, tfidf_similarity]:", clf.coef_)
    print("Intercept:", clf.intercept_)

    # 5) Simpan artefak
    import os
    os.makedirs(out_dir, exist_ok=True)

    with open(f"{out_dir}/skill_vocab.json", "w", encoding="utf-8") as f:
        json.dump(skill_vocab, f, ensure_ascii=False, indent=2)

    joblib.dump(vectorizer, f"{out_dir}/tfidf_vectorizer.joblib")
    joblib.dump(clf, f"{out_dir}/match_classifier.joblib")

    print(f"\nArtefak disimpan di folder: {out_dir}/")
    print("- skill_vocab.json")
    print("- tfidf_vectorizer.joblib")
    print("- match_classifier.joblib")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Career Match model.")
    parser.add_argument("--data", default="data/jobs_processed.csv")
    parser.add_argument("--out_dir", default="models")
    args = parser.parse_args()

    main(args.data, args.out_dir)
