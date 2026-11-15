# Pemetaan Kepatuhan UU PDP No. 27 Tahun 2022

Dokumen ini menjelaskan korelasi langsung antara pasal-pasal dalam **Undang-Undang No. 27 Tahun 2022 tentang Pelindungan Data Pribadi (UU PDP)** dengan fitur teknis yang diimplementasikan pada **DataShield-PDP**.

---

## Matriks Kepatuhan (Compliance Matrix)

| No | Pasal UU PDP | Ketentuan Regulasi | Solusi Teknis DataShield-PDP | Verifikasi / Bukti Kepatuhan |
|---|---|---|---|---|
| 1 | **Pasal 16 Ayat (2) Huruf b** | Pemrosesan Data Pribadi dilakukan secara terbatas dan spesifik, sah secara hukum, dan transparan. | **Automated Data Catalog & Tagging:** Setiap kolom data pribadi secara otomatis diinventarisasi, diberi label sensitivitas, dan dibatasi hanya untuk pemrosesan yang sah. | Tabel `pii_catalog` di database metadata. |
| 2 | **Pasal 16 Ayat (2) Huruf f** | Pemrosesan Data Pribadi dilakukan dengan melindungi keamanan Data Pribadi dari kehilangan, penyalahgunaan, dan pengubahan tanpa hak. | **Anonymization & Masking Engine:** Mengubah data pribadi menjadi format pseudonim (*Salted Hash*) dan *Masked String* sebelum dikonsumsi oleh tim internal. | Tabel `customers_anonymized` di mana NIK dan nomor kontak tidak tampil telanjang. |
| 3 | **Pasal 35** | Pengendali Data Pribadi wajib melindungi dan memastikan keamanan Data Pribadi yang diprosesnya melalui langkah teknis dan operasional. | **Role-Based Access Control (RBAC):** Membatasi akses data langsung. Tim analitik hanya memiliki akses ke layer mart yang sudah di-mask. | Modul `audit_logger.py` dan verifikasi hak akses per role. |
| 4 | **Pasal 39** | Pengendali Data Pribadi wajib mencegah Data Pribadi diakses secara tidak sah dengan menerapkan sistem enkripsi dan/atau teknik pseudonimisasi. | **Cryptographic Salted Hashing (HMAC-SHA256):** Menerapkan standar pseudonimisasi yang diakui secara global (*cryptographically strong*). | Fungsi `hash_pseudonym()` pada modul `apply_masking.py`. |
| 5 | **Pasal 47** | Pengendali Data Pribadi wajib merekam seluruh kegiatan pemrosesan Data Pribadi. | **Immutable Audit Trail:** Setiap pembacaan data, running scan, dan export data dicatat dengan timestamp, User ID, dan tipe query. | Tabel `audit_access_log` yang dapat diinspeksi oleh auditor kapan saja. |

---

## Kesimpulan untuk DPO dan Auditor

Dengan implementasi DataShield-PDP, organisasi memiliki bukti konkret (*demonstrable accountability*) bahwa prinsip **Privacy by Design** dan **Privacy by Default** telah diterapkan pada alur data internal.
