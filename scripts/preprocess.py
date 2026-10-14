
"""Preprocessing pipeline untuk dataset lowongan Glints."""

import argparse
import json
import re
import unicodedata
from urllib.parse import urlsplit, urlunsplit

import pandas as pd


ROLE_KEYWORDS = {
    "software-engineering": [
        "software engineer", "backend", "back-end", "frontend",
        "front-end", "full stack", "developer", "programmer",
        "web developer", "mobile developer", "android", "ios developer"
    ],
    "data-ai": [
        "data analyst", "data scientist", "data engineer", "data entry analyst",
        "machine learning", "artificial intelligence", "business intelligence",
        "data science"
    ],
    "qa-security": [
        "quality assurance", "qa engineer", "software tester",
        "penetration test", "cyber security", "security analyst", "quality control"
    ],
    "it-support-network": [
        "it support", "technical support", "network engineer",
        "system administrator", "help desk", "helpdesk", "it technical",
        "troubleshooting", "it staff"
    ],
    "product-project-business": [
        "product manager", "project manager", "business analyst",
        "product owner", "scrum master"
    ],
    "design-content": [
        "designer", "design", "content writer", "content creator",
        "copywriter", "video editor", "social media", "kol specialist",
        "host live", "streamer"
    ],
    "engineering-technical": [
        "engineer", "engineering", "teknisi", "maintenance",
        "electrical", "mechanical", "civil engineer", "hse"
    ],
    "hospitality-service": [
        "waiter", "waitress", "cook", "chef", "housekeeping",
        "hotel", "restaurant", "hospitality", "beautician", "therapist",
        "barista", "crew outlet"
    ],
    "sales-account": [
        "sales", "marketing", "account executive",
        "business development", "telemarketing"
    ],
    "admin-operations": [
        "admin", "administrasi", "administrator", "operational",
        "operasional", "operator", "customer service", "cs/",
        "finance", "accounting", "warehouse", "logistik",
        "data entry", "purchasing", "helper", "resepsionis",
        "receptionist", "cashier"
    ],
}

EDU = [
    (["magister", "master", "s2"], "master"),
    (["sarjana", "bachelor", "s1"], "bachelor"),
    (["diploma", "d3", "d4", "d1", "d2"], "diploma"),
    (["sma", "smk", "senior high", "vocational"], "high school"),
    (["smp", "junior high"], "junior high"),
]

EDU_ORDER = {
    "not specified": 0,
    "junior high": 1,
    "high school": 2,
    "diploma": 3,
    "bachelor": 4,
    "master": 5,
}

# Istilah yang tidak boleh dipotong pada batas huruf kecil -> huruf besar.
PROTECTED_TERMS = [
    "iOS", "eCommerce", "YouTube", "PowerPoint",
    "JavaScript", "LinkedIn", "TikTok", "GitHub",
]


def clean(value):
    """Membersihkan nilai kosong dan karakter teks."""
    if value is None or pd.isna(value):
        return ""

    text = unicodedata.normalize("NFKC", str(value))
    text = text.replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def normalize_url(url):
    """Menghapus parameter tracking agar duplikat URL lebih mudah dikenali."""
    url = clean(url)

    if not url:
        return ""

    try:
        parts = urlsplit(url)

        if not parts.scheme or not parts.netloc:
            return url

        return urlunsplit((
            parts.scheme.lower(),
            parts.netloc.lower(),
            parts.path.rstrip("/"),
            "",
            "",
        ))

    except Exception:
        return url



def split_skills(raw):
    """Memisahkan skill Glints yang menempel tanpa merusak nama skill."""
    text = clean(raw)

    if not text:
        return []

    # Pisahkan setelah istilah khusus jika langsung diikuti huruf kapital.
    # Contoh: TikTokGoogle Analytics -> TikTok | Google Analytics
    for term in sorted(PROTECTED_TERMS, key=len, reverse=True):
        pattern = rf"({re.escape(term)})(?=[A-Z])"
        text = re.sub(pattern, r"\1|", text)

    # Lindungi istilah dengan kapitalisasi khusus.
    protected = {}

    for i, term in enumerate(PROTECTED_TERMS):
        token = f"SKILLPROTECTED{i}TOKEN"
        if term in text:
            text = text.replace(term, token)
            protected[token] = term

    # Pisahkan batas kata yang menempel.
    # Contoh: StrategyMarketing -> Strategy|Marketing
    text = re.sub(r"(?<=[a-z])(?=[A-Z])", "|", text)

    # Pisahkan setelah tanda kurung penutup jika langsung diikuti skill baru.
    # Contoh: Point of Sales)Customer Service
    text = re.sub(r"(?<=[)\]])(?=[A-Z])", "|", text)

    # Pisahkan berdasarkan delimiter yang umum ditemukan.
    chunks = re.split(r"[|;,\n\r]+", text)

    result = []
    seen = set()

    for chunk in chunks:
        chunk = clean(chunk)

        if not chunk:
            continue

        # Pulihkan istilah khusus.
        for token, term in protected.items():
            chunk = chunk.replace(token, term)

        chunk = re.sub(r"\s+", " ", chunk).strip(" .:-")

        if not chunk:
            continue

        key = chunk.casefold()

        if key not in seen:
            seen.add(key)
            result.append(chunk)

    return result


def exp_years(raw):
    """Mengambil batas pengalaman kerja dalam tahun."""
    text = clean(raw).lower()

    if not text:
        return None, None

    if any(term in text for term in [
        "kurang dari 1 tahun", "less than a year",
        "fresh graduate", "no experience", "tanpa pengalaman"
    ]):
        return 0.0, 1.0

    patterns = [
        r"(\d+(?:[.,]\d+)?)\s*[-–—sampai]+\s*(\d+(?:[.,]\d+)?)\s*tahun",
        r"(\d+(?:[.,]\d+)?)\s*[-–—]\s*(\d+(?:[.,]\d+)?)\s*years?",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            minimum = float(match.group(1).replace(",", "."))
            maximum = float(match.group(2).replace(",", "."))
            return min(minimum, maximum), max(minimum, maximum)

    match = re.search(
        r"(\d+(?:[.,]\d+)?)\s*\+?\s*tahun(?:\s+pengalaman)?",
        text
    )

    if not match:
        match = re.search(
            r"(\d+(?:[.,]\d+)?)\s*\+?\s*years?\s*(?:of\s+experience)?",
            text
        )

    if match:
        years = float(match.group(1).replace(",", "."))
        return years, years if "+" not in match.group(0) else None

    return None, None


def role_family(title):
    """Menentukan kategori pekerjaan berdasarkan judul."""
    text = clean(title).lower()

    # Periksa keyword yang lebih spesifik terlebih dahulu.
    for family, keywords in ROLE_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return family

    if any(keyword in text for keyword in [
        "cloud", "devops", "programming", "information technology"
    ]):
        return "it-support-network"

    return "other"


def get_work_mode(job_type):
    text = clean(job_type).lower()

    if "hybrid" in text:
        return "hybrid"

    if any(term in text for term in [
        "remote", "dari rumah", "jarak jauh", "work from home"
    ]):
        return "remote"

    if any(term in text for term in [
        "kerja di lokasi", "on-site", "onsite", "di kantor"
    ]):
        return "onsite"

    return "unknown"


def education_level(education, requirements, description=""):
    text = " ".join([
        clean(education),
        clean(requirements),
        clean(description),
    ]).lower()

    # Cek SMA/SMK sebelum S1 agar kata SMK tidak salah terbaca sebagai S1.
    for keywords, label in EDU:
        if any(re.search(
            rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])",
            text
        ) for keyword in keywords):
            return label

    return "not specified"


def extract_city(location):
    """Mengambil kota dari alamat bila informasi kota dapat dikenali."""
    text = clean(location)

    if not text:
        return ""

    # Contoh: Kota Jakarta Barat atau Kota Adm. Jakarta Utara.
    match = re.search(
        r"\bKota(?:\s+Adm\.)?\s+([^,\n]+)",
        text,
        flags=re.IGNORECASE
    )

    if match:
        return clean(match.group(1))

    # Contoh: Kabupaten Sleman.
    match = re.search(
        r"\bKabupaten\s+([^,\n]+)",
        text,
        flags=re.IGNORECASE
    )

    if match:
        return clean(match.group(1))

    # Cadangan: kota yang sering muncul dalam dataset Indonesia.
    known_cities = [
        "Jakarta Selatan", "Jakarta Barat", "Jakarta Timur",
        "Jakarta Utara", "Jakarta Pusat", "Kota Jakarta",
        "Surabaya", "Bandung", "Semarang", "Yogyakarta",
        "Malang", "Madiun", "Sidoarjo", "Bekasi", "Depok",
        "Tangerang Selatan", "Tangerang", "Bogor", "Medan",
        "Makassar", "Denpasar", "Palembang", "Balikpapan",
        "Sleman", "Gresik", "Cikarang",
    ]

    lower_text = text.lower()

    for city in sorted(known_cities, key=len, reverse=True):
        if city.lower() in lower_text:
            return city

    # Jangan menebak kota jika alamat tidak cukup jelas.
    return ""


def preprocess(input_path, output_path):
    # Baca dataset mentah.
    
    if input_path.lower().endswith((".xlsx", ".xls")):
        df = pd.read_excel(input_path)
    else:
        # Deteksi pemisah CSV secara otomatis.
        df = pd.read_csv(input_path, sep=None, engine="python")


    df.columns = df.columns.str.strip()

    required = ["job_title", "company", "job_links"]
    missing = [col for col in required if col not in df.columns]

    if missing:
        raise ValueError(f"Kolom wajib tidak ditemukan: {missing}")

    # Siapkan kolom yang mungkin belum tersedia.
    source_columns = [
        "location", "salary", "job_type", "education",
        "experience", "requirements", "skills", "benefits",
        "description"
    ]

    for col in source_columns:
        if col not in df.columns:
            df[col] = ""

        df[col] = df[col].map(clean)

    # Buang baris tanpa judul pekerjaan atau URL.
    df = df[
        df["job_title"].ne("") & df["job_links"].ne("")
    ].copy()

    # Deduplikasi URL tanpa parameter tracking.
    df["_normalized_url"] = df["job_links"].map(normalize_url)
    df = df.drop_duplicates(
        subset=["_normalized_url"], keep="first"
    ).copy()

    df = df.reset_index(drop=True)

    # Identitas lowongan.
    df["job_id"] = ["glints-" + str(i + 1) for i in range(len(df))]
    df["source"] = "Glints"
    df["job_detail"] = df["job_links"]

    # Skill tetap utuh, disimpan sebagai JSON dan teks gabungan.
    df["skills"] = df["skills"].apply(split_skills)
    df["skills_joined"] = df["skills"].apply(
        lambda items: ", ".join(items)
    )

    # Informasi pengalaman.
    experience_values = df["experience"].apply(exp_years)
    df["min_experience_years"] = experience_values.apply(lambda x: x[0])
    df["max_experience_years"] = experience_values.apply(lambda x: x[1])

    # Pendidikan.
    df["education_required"] = df.apply(
        lambda row: education_level(
            row["education"],
            row["requirements"],
            row["description"]
        ),
        axis=1
    )

    df["education_level_required"] = (
        df["education_required"].map(EDU_ORDER).fillna(0).astype(int)
    )

    # Mode kerja dan kota.
    df["work_mode"] = df["job_type"].apply(get_work_mode)
    df["city"] = df["location"].apply(extract_city)

    # Sertifikasi yang disebutkan dalam teks lowongan.
    certification_keywords = [
        "toefl", "ielts", "pmp", "aws certified",
        "google certified", "cisco", "ccna", "comptia",
        "brevet pajak", "k3"
    ]

    def extract_certifications(row):
        text = (
            clean(row["requirements"]) + " " +
            clean(row["description"])
        ).lower()

        return [
            cert for cert in certification_keywords
            if cert in text
        ]

    df["certifications_required"] = df.apply(
        extract_certifications, axis=1
    )
    df["certifications_required_joined"] = (
        df["certifications_required"].apply(lambda x: ", ".join(x))
    )

    # Kategori pekerjaan.
    df["role_family"] = df["job_title"].apply(role_family)

    # Gabungkan teks untuk model rekomendasi.
    def build_job_text(row):
        fields = [
            ("Posisi", row["job_title"]),
            ("Perusahaan", row["company"]),
            ("Lokasi", row["location"]),
            ("Gaji", row["salary"]),
            ("Jenis pekerjaan", row["job_type"]),
            ("Mode kerja", row["work_mode"]),
            ("Pendidikan", row["education_required"]),
            ("Pengalaman", row["experience"]),
            ("Skills", row["skills_joined"]),
            ("Requirements", row["requirements"]),
            ("Deskripsi", row["description"]),
            ("Benefit", row["benefits"]),
        ]

        return ". ".join(
            f"{label}: {clean(value)}"
            for label, value in fields
            if clean(value)
        )

    df["job_text"] = df.apply(build_job_text, axis=1)

    # Pertahankan nama kolom yang digunakan pipeline lama.
    out = df[[
        "job_id", "source", "job_title", "company", "location", "city",
        "job_detail", "description", "requirements", "skills_joined",
        "skills", "certifications_required_joined", "benefits",
        "min_experience_years", "max_experience_years",
        "education_level_required", "education_required", "work_mode",
        "role_family", "job_text", "salary", "job_type", "experience",
        "job_links"
    ]].copy()

    out = out.rename(columns={"benefits": "job_benefits"})

    # Simpan daftar skill sebagai JSON yang valid.
    out["skills"] = out["skills"].apply(
        lambda items: json.dumps(items, ensure_ascii=False)
    )

    out.to_csv(output_path, index=False, encoding="utf-8-sig")

    total_skills = sum(
        len(json.loads(value)) for value in out["skills"]
    )

    print(f"Selesai preprocessing: {len(out)} lowongan")
    print(f"File output: {output_path}")
    print(f"Role family: {out['role_family'].nunique()}")
    print(f"Total skill tags: {total_skills}")
    print(f"Kota berhasil dikenali: {(out['city'] != '').sum()}")

    print("\nContoh hasil ekstraksi skill:")
    for _, row in out.head(5).iterrows():
        print(f"- {row['job_title']}: {row['skills_joined']}")

    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default="data/glints_job_3.csv"
    )
    parser.add_argument(
        "--output",
        default="data/jobs_processed.csv"
    )

    args = parser.parse_args()
    preprocess(args.input, args.output)
