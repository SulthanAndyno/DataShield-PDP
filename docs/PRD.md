# Product Requirement Document (PRD)

## Project Name: DataShield-PDP
**Automated PII Scanner, Dynamic Masking & UU PDP Compliance Framework**

---

| Metadata | Details |
| :--- | :--- |
| **Document Version** | v1.0.0 |
| **Status** | Approved / Production Ready |
| **Author / Lead** | Data Governance & Engineering Team |
| **Target Regulation** | UU No. 27 Tahun 2022 tentang Pelindungan Data Pribadi (UU PDP) |
| **Target Users** | Data Engineers, Data Analysts, DPO (Data Protection Officer), Compliance Auditors |

---

## 1. Executive Summary & Problem Statement

### 1.1 Latar Belakang & Urgensi Bisnis
Dengan disahkannya **Undang-Undang No. 27 Tahun 2022 tentang Pelindungan Data Pribadi (UU PDP)** di Indonesia, setiap pengendali data wajib menjamin kerahasiaan dan keamanan Data Pribadi yang diproses. Sanksi pelanggaran mencakup:
- Denda administratif hingga **2% dari total pendapatan tahunan**.
- Pidana penjara dan ganti rugi perdata.
- Kerusakan reputasi brand akibat kebocoran data (*data breach*).

### 1.2 Problem Statement
Di sebagian besar organisasi, *Data Warehouse* (DWH) atau *Data Lake* mengumpulkan data mentah dari sistem transaksional. Tanpa kontrol tata kelola:
1. **Unidentified Sensitive Data:** Tim data tidak tahu persis kolom mana saja di ratusan tabel yang menyimpan NIK, nomor telepon, atau data finansial.
2. **Over-privileged Access:** Tim Data Analyst atau Machine Learning Engineer memiliki akses langsung (*SELECT \**) ke data produksi mentah tanpa proteksi masking.
3. **Absence of Audit Trail:** Tidak ada jejak audit (*audit trail*) otomatis yang membuktikan bahwa pemrosesan data sudah sesuai regulasi saat audit independen dilakukan.

### 1.3 Solusi yang Ditawarkan
Membangun sistem otomasi *open-source* bernama **DataShield-PDP** yang:
1. Menemukan data pribadi (*PII Scanner*) secara otomatis menggunakan kombinasi NLP dan pola spesifik Indonesia (NIK, NPWP, No HP).
2. Melakukan *masking* dan pseudonimisasi secara terprogram sebelum data masuk ke layer analitik.
3. Menyediakan kontrol akses berbasis peran (RBAC).
4. Menyediakan dashboard kepatuhan (*Compliance Scorecard*) untuk DPO dan auditor.

---

## 2. Goals & Success Metrics (OKRs)

### 2.1 Objectives
1. Mengurangi risiko keterpaparan data sensitif di lingkungan analytics/data science hingga mendekati nol.
2. Mengotomatisasi inventarisasi data pribadi (*PII Data Catalog*) tanpa intervensi manual.
3. Memastikan kepatuhan terhadap prinsip *Privacy by Design* sesuai UU PDP.

### 2.2 Key Performance Indicators (KPIs)
| Metric | Baseline | Target |
| :--- | :--- | :--- |
| **PII Detection Accuracy (F1-Score)** | Manual / 0% | $\ge 95\%$ untuk entitas spesifik Indonesia |
| **PII Masking Coverage** | 0% | $100\%$ tabel analitik sensitif ter-mask |
| **Audit Compliance Readiness** | Butuh 2 minggu audit | Realtime via Compliance Dashboard |
| **Pipeline Performance Overhead** | N/A | Masking overhead $< 15\%$ total waktu pipeline ETL |

---

## 3. Scope of Work

### 3.1 In-Scope (MVP)
- **Synthetic Data Generator:** Modul penghasil data dummy realistis (pelanggan Indonesia: NIK, nama lokal, no HP +62, email, alamat).
- **Indonesian PII Recognizers:** Ekstensi custom pada Microsoft Presidio untuk mendeteksi NIK, NPWP, dan Nomor Telepon Indonesia.
- **Multi-Method Anonymization Engine:**
  - *Redaction* (penghapusan total: `[REDACTED]`).
  - *Partial Masking* (misal: `320101********01`).
  - *Cryptographic Hashing* (SHA-256 + Salt untuk keperluan join analytics tanpa mengekspos raw identity).
- **Automated Data Catalog & Tagging:** Output metadata dalam format SQLite/JSON yang mencatat tabel, kolom, jenis PII, dan tingkat sensitivitas.
- **Role-Based Access Simulation (RBAC):** Pemisahan akses antara role `Data_Analyst` (masked data) dan `DPO` (raw data dengan audit log).
- **Interactive UI Dashboard:** Streamlit dashboard untuk visualisasi postur kepatuhan data.

---

## 4. Legal & Safety Assessment

> [!NOTE]
> **Status Keamanan: 100% AMAN & LEGAL**
> 1. **Synthetic Data Only:** Proyek ini menggunakan 100% data buatan (mock/dummy) yang digenerate oleh algoritma komputer. Tidak ada data pribadi warga negara yang diambil, disimpan, atau disalahgunakan.
> 2. **Defensive Security & Compliance:** Proyek ini berfokus pada teknologi *defensif* (perlindungan privasi, enkripsi, kepatuhan hukum), yang merupakan standar kompetensi resmi bagi profesional Data Governance, Cyber Security, dan Data Privacy Engineer di industri global.
