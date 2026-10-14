# Career Match — Glints Job Recommendation

Aplikasi Streamlit untuk:
- **CV Screening:** membandingkan CV PDF dengan deskripsi pekerjaan yang ditempel.
- **Career Match:** merekomendasikan lowongan dari dataset Glints terbaru berdasarkan isi CV.

## Dataset baru
Sumber data: `data/glints_job_3.csv` (dari file `glints_job_3.xlsx` yang diunggah).
Dataset berisi 2.658 lowongan dan kolom seperti judul, perusahaan, lokasi, gaji, tipe pekerjaan, pendidikan, pengalaman, skills, requirements, benefits, serta deskripsi dan tautan Glints.

Data katalog lama sudah diganti. File `data/jobs_processed.csv` dibuat ulang dari dataset baru, dan seluruh artefak model di `models/` dilatih ulang dari data hasil preprocessing tersebut.

## Jalankan aplikasi
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Ulangi preprocessing dan training
Jalankan dari folder `career_match_app/`:
```bash
python scripts/preprocess.py --input data/glints_job_3.csv --output data/jobs_processed.csv
python scripts/train_model.py --data data/jobs_processed.csv --out_dir models
streamlit run app.py
```

## Alur
1. **Preprocessing:** menghapus duplikasi berdasarkan `job_links`, merapikan skills yang menempel, menormalkan pendidikan, pengalaman, mode kerja, dan kategori peran.
2. **TF-IDF:** mempelajari representasi teks dari `job_text` semua lowongan.
3. **Training:** Logistic Regression memprediksi kecocokan dari skill overlap dan cosine similarity. Label training dibuat melalui weak supervision: skill lowongan sendiri dianggap pasangan positif, sedangkan skill dari kategori peran berbeda dijadikan pasangan negatif.
4. **Career Match:** mengekstrak kata kunci/skills dari CV, menghitung skor terhadap seluruh katalog Glints, lalu menampilkan rekomendasi beserta detail dan tautan lowongan.

## Catatan evaluasi
Akurasi pengujian yang sangat tinggi pada pipeline ini tidak boleh dianggap sebagai akurasi nyata seleksi kandidat. Label dibuat secara sintetis dengan aturan yang memisahkan pasangan positif dan negatif, sehingga hasil evaluasi terutama menunjukkan bahwa model mempelajari pola label tersebut. Untuk mengukur kinerja nyata, model perlu diuji dengan pasangan CV-lowongan yang dinilai oleh manusia atau data hasil rekrutmen.
