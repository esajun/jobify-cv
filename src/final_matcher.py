"""
final_matcher.py
-----------------
Modul untuk menggabungkan requirement score & semantic score menjadi
skor akhir, lalu menerjemahkannya menjadi rekomendasi dan penjelasan
yang mudah dibaca manusia (recruiter/user).
"""

# Bobot masing-masing komponen skor. Total harus 1.0.
# Requirement score diberi bobot lebih besar karena mencerminkan
# kecocokan skill secara eksplisit, sedangkan semantic score
# menangkap kemiripan konteks/istilah secara umum.
WEIGHT_REQUIREMENT = 0.6
WEIGHT_SEMANTIC = 0.4


def calculate_final_score(requirement_score: float, semantic_score: float) -> float:
    """
    Menggabungkan requirement score dan semantic score menjadi satu skor akhir
    menggunakan rata-rata berbobot.

    Args:
        requirement_score: skor kecocokan requirement (0-100).
        semantic_score: skor kemiripan semantik (0-100).

    Returns:
        Skor akhir (0-100), dibulatkan 2 desimal.
    """
    final = (requirement_score * WEIGHT_REQUIREMENT) + (semantic_score * WEIGHT_SEMANTIC)
    return round(final, 2)


def generate_recommendation(final_score: float) -> str:
    """
    Menerjemahkan skor akhir menjadi label rekomendasi.

    Args:
        final_score: skor akhir (0-100).

    Returns:
        String rekomendasi.
    """
    if final_score >= 75:
        return "✅ Sangat Direkomendasikan — kandidat sangat sesuai dengan kebutuhan posisi ini."
    elif final_score >= 50:
        return "🟡 Layak Dipertimbangkan — kandidat cukup sesuai, namun ada beberapa gap yang perlu ditinjau."
    else:
        return "🔴 Kurang Sesuai — kandidat memiliki gap signifikan terhadap requirement posisi ini."


def generate_explanation(matched: list, missing: list) -> str:
    """
    Membuat penjelasan naratif singkat berdasarkan skill yang cocok dan yang hilang.

    Args:
        matched: list skill yang ada di CV maupun job description.
        missing: list skill yang diminta job description tapi tidak ada di CV.

    Returns:
        String penjelasan.
    """
    if not matched and not missing:
        return (
            "Tidak cukup informasi skill yang terdeteksi baik dari CV maupun "
            "job description untuk dianalisis lebih lanjut."
        )

    parts = []

    if matched:
        top_matched = ", ".join(matched[:5])
        parts.append(
            f"Kandidat menunjukkan kecocokan pada {len(matched)} skill/kata kunci, "
            f"di antaranya: {top_matched}."
        )
    else:
        parts.append("Tidak ditemukan kecocokan skill yang eksplisit antara CV dan job description.")

    if missing:
        top_missing = ", ".join(missing[:5])
        parts.append(
            f"Namun, terdapat {len(missing)} requirement yang belum terlihat jelas di CV, "
            f"seperti: {top_missing}."
        )
    else:
        parts.append("Tidak ada gap requirement yang signifikan terdeteksi.")

    return " ".join(parts)
