"""
resume_parser.py
-----------------
Modul sederhana untuk mengekstrak teks mentah dari file CV berformat PDF.
Menggunakan pdfplumber karena ringan dan cukup akurat untuk CV berbasis teks
(bukan hasil scan/gambar).
"""

import pdfplumber


def extract_text_from_pdf(file_path: str) -> str:
    """
    Membaca file PDF dan mengembalikan seluruh isinya sebagai satu string.

    Args:
        file_path: path menuju file PDF (bisa file temporary hasil upload Streamlit).

    Returns:
        String berisi seluruh teks yang berhasil diekstrak dari PDF.
        Jika PDF tidak memiliki teks (misalnya hasil scan tanpa OCR),
        akan mengembalikan string kosong.
    """
    full_text = []

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text.append(text)

    return "\n".join(full_text)
