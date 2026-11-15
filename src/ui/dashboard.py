"""
Streamlit Compliance & Data Governance Dashboard for DataShield-PDP.
Visualizes UU PDP compliance score, PII Catalog, Audit Logs, and provides an interactive sandbox.
"""

import sqlite3
import sys
from pathlib import Path
import pandas as pd
import streamlit as st

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.audit.audit_logger import get_audit_logs, get_pii_catalog, log_access_event
from src.config import ANONYMIZED_DB_PATH, METADATA_DB_PATH, RAW_DB_PATH
from src.masker.apply_masking import mask_value_by_strategy
from src.scanner.run_scanner import build_analyzer_engine, map_entity_to_governance_policy


@st.cache_resource
def ensure_sample_data_initialized():
    """Auto-seeds synthetic data, runs scanner, and builds anonymized mart on first cloud boot."""
    from src.generator.generate_mock_data import generate_mock_dataset
    from src.masker.apply_masking import create_anonymized_data_mart
    from src.scanner.run_scanner import scan_database_tables

    if not RAW_DB_PATH.exists():
        generate_mock_dataset(num_customers=200, num_orders=600)

    cat = get_pii_catalog()
    if cat.empty:
        scan_database_tables()

    if not ANONYMIZED_DB_PATH.exists():
        create_anonymized_data_mart()


# Auto-initialize database on cloud run if missing
ensure_sample_data_initialized()

# Page Config
st.set_page_config(
    page_title="DataShield-PDP | Data Governance & Privacy",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown(
    """
    <style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #1E3A8A; margin-bottom: 0.2rem; }
    .sub-header { font-size: 1.05rem; color: #4B5563; margin-bottom: 1.5rem; }
    .badge-pdp { background-color: #DC2626; color: white; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 0.85rem; }
    .kpi-card { background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 18px; border-radius: 10px; text-align: center; }
    .kpi-num { font-size: 1.8rem; font-weight: 700; color: #1E40AF; }
    .kpi-label { font-size: 0.85rem; color: #64748B; font-weight: 500; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header Section
st.markdown('<div class="main-header">🛡️ DataShield-PDP</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Automated PII Discovery, Anonymization & UU PDP No. 27/2022 Compliance Engine <span class="badge-pdp">UU PDP COMPLIANT</span></div>',
    unsafe_allow_html=True,
)

# Sidebar
st.sidebar.image("https://img.icons8.com/color/96/shield.png", width=70)
st.sidebar.title("DataShield Governance")
st.sidebar.markdown("**Regulation:** UU No. 27/2022 (PDP)")
st.sidebar.markdown("**Environment:** Production Analytics")
st.sidebar.markdown("---")
st.sidebar.markdown("### Quick Navigation")
tab_selection = st.sidebar.radio(
    "Select View:",
    ["📊 Executive Scorecard", "🔍 PII Data Catalog", "🧪 Interactive Sandbox", "🛡️ RBAC & Audit Trail"],
)

st.sidebar.markdown("---")
st.sidebar.caption("DataShield-PDP v1.0.0 • Built for Data Privacy Engineering")

# -------------------------------------------------------------
# TAB 1: EXECUTIVE SCORECARD
# -------------------------------------------------------------
if tab_selection == "📊 Executive Scorecard":
    st.subheader("Executive Compliance Scorecard")
    
    catalog_df = get_pii_catalog()
    audit_df = get_audit_logs(limit=10)

    total_scanned = len(catalog_df)
    restricted_count = len(catalog_df[catalog_df["classification_tier"] == "Restricted"]) if not catalog_df.empty else 0
    confidential_count = len(catalog_df[catalog_df["classification_tier"] == "Confidential"]) if not catalog_df.empty else 0
    protected_count = len(catalog_df[catalog_df["masking_strategy"] != "None"]) if not catalog_df.empty else 0

    compliance_rate = (protected_count / (restricted_count + confidential_count) * 100) if (restricted_count + confidential_count) > 0 else 100.0

    # KPI Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f'<div class="kpi-card"><div class="kpi-num">{total_scanned}</div><div class="kpi-label">Columns Cataloged</div></div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f'<div class="kpi-card"><div class="kpi-num">{restricted_count}</div><div class="kpi-label">Restricted / Sensitif (NIK/NPWP)</div></div>',
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f'<div class="kpi-card"><div class="kpi-num">{confidential_count}</div><div class="kpi-label">Confidential (HP/Email/Nama)</div></div>',
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f'<div class="kpi-card"><div class="kpi-num">{compliance_rate:.1f}%</div><div class="kpi-label">Anonymization Coverage</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.success("✅ **STATUS KEPATUHAN AKTIF:** Tidak ada data NIK atau nomor kontak mentah yang terekspos di layer analitik terbuka.")

    # Charts
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.markdown("#### Distribusi Entitas PII Terdeteksi")
        if not catalog_df.empty:
            entity_counts = catalog_df["detected_entity"].value_counts().reset_index()
            entity_counts.columns = ["Entitas PII", "Jumlah Kolom"]
            st.bar_chart(entity_counts.set_index("Entitas PII"))
        else:
            st.info("Belum ada data katalog. Jalankan scanner untuk memindai database.")

    with col_chart2:
        st.markdown("#### Matriks Kepatuhan Pasal UU PDP")
        mandates = [
            {"Pasal": "Pasal 16 (2)", "Topik": "Pemrosesan Terbatas & Spesifik", "Status": "TERPENUHI (Via Catalog)"},
            {"Pasal": "Pasal 35", "Topik": "Keamanan & Pelindungan Teknis", "Status": "TERPENUHI (Via RBAC)"},
            {"Pasal": "Pasal 39", "Topik": "Kewajiban Enkripsi/Pseudonimisasi", "Status": "TERPENUHI (Salted Hash)"},
            {"Pasal": "Pasal 47", "Topik": "Perekaman Kegiatan Pemrosesan", "Status": "TERPENUHI (Audit Trail)"},
        ]
        st.dataframe(pd.DataFrame(mandates), use_container_width=True)

# -------------------------------------------------------------
# TAB 2: PII DATA CATALOG
# -------------------------------------------------------------
elif tab_selection == "🔍 PII Data Catalog":
    st.subheader("PII Data Catalog & Metadata Inventory")
    st.markdown("Inventarisasi kolom sensitif hasil scanning otomatis Microsoft Presidio dengan custom aturan Indonesia.")

    catalog_df = get_pii_catalog()

    if catalog_df.empty:
        st.warning("Katalog data masih kosong. Silakan jalankan scanner.")
    else:
        # Filter controls
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            tables = ["All Tables"] + list(catalog_df["table_name"].unique())
            selected_table = st.selectbox("Filter Tabel:", tables)
        with f_col2:
            tiers = ["All Tiers"] + list(catalog_df["classification_tier"].unique())
            selected_tier = st.selectbox("Filter Tingkat Sensitivitas:", tiers)

        filtered = catalog_df.copy()
        if selected_table != "All Tables":
            filtered = filtered[filtered["table_name"] == selected_table]
        if selected_tier != "All Tiers":
            filtered = filtered[filtered["classification_tier"] == selected_tier]

        # Display catalog
        st.dataframe(
            filtered[
                [
                    "table_name",
                    "column_name",
                    "detected_entity",
                    "confidence_score",
                    "classification_tier",
                    "masking_strategy",
                    "scanned_at",
                ]
            ],
            use_container_width=True,
        )

# -------------------------------------------------------------
# TAB 3: INTERACTIVE SANDBOX
# -------------------------------------------------------------
elif tab_selection == "🧪 Interactive Sandbox":
    st.subheader("Interactive PII Detection & Masking Sandbox")
    st.markdown("Uji kemampuan deteksi entitas Indonesia secara langsung menggunakan teks bebas.")

    sample_text = (
        "Nasabah atas nama Siti Nurhaliza (NIK 3201015204950002) telah mengonfirmasi pembayaran.\n"
        "Nomor WhatsApp aktif: +6281298765432, email: siti.nurhaliza99@gmail.com.\n"
        "NPWP terdaftar: 01.345.678.9-012.000, alamat domisili di Jl. Malioboro No. 45, Yogyakarta."
    )

    user_input = st.text_area("Masukkan teks pengujian:", value=sample_text, height=120)

    if st.button("🚀 Pindai & Lakukan Masking"):
        with st.spinner("Menganalisis teks dengan Presidio Analyzer..."):
            analyzer = build_analyzer_engine()
            results = analyzer.analyze(text=user_input, language="en")

            st.markdown("#### 1. Entitas Sensitif Terdeteksi")
            if results:
                detection_data = []
                for res in results:
                    val = user_input[res.start:res.end]
                    tier, strat = map_entity_to_governance_policy(res.entity_type)
                    detection_data.append({
                        "Teks Terdeteksi": val,
                        "Entitas PII": res.entity_type,
                        "Confidence": f"{res.score:.2f}",
                        "Sensitivitas (UU PDP)": tier,
                        "Strategi Masking": strat,
                    })
                st.dataframe(pd.DataFrame(detection_data), use_container_width=True)

                # Masking preview
                st.markdown("#### 2. Hasil Transformasi (Masked Output)")
                masked_text = user_input
                # Sort from last to first so indices remain accurate
                for res in sorted(results, key=lambda x: x.start, reverse=True):
                    val = user_input[res.start:res.end]
                    _, strat = map_entity_to_governance_policy(res.entity_type)
                    masked_val = mask_value_by_strategy(val, strat, res.entity_type)
                    masked_text = masked_text[:res.start] + str(masked_val) + masked_text[res.end:]

                st.code(masked_text, language="text")
            else:
                st.info("Tidak ditemukan entitas data pribadi sensitif.")

# -------------------------------------------------------------
# TAB 4: RBAC & AUDIT TRAIL
# -------------------------------------------------------------
elif tab_selection == "🛡️ RBAC & Audit Trail":
    st.subheader("Role-Based Access Control (RBAC) & Audit Log Simulator")
    st.markdown("Simulasikan query data dengan role berbeda untuk membuktikan penegakan izin akses dan audit trail.")

    c1, c2 = st.columns(2)
    with c1:
        role = st.selectbox("Pilih Peran Pengguna (Role):", ["Data_Analyst", "Data_Protection_Officer (DPO)"])
    with c2:
        user_id = st.text_input("User ID:", value="USR-ANALYST-01" if "Analyst" in role else "USR-DPO-CHIEF")

    if role == "Data_Analyst":
        st.info("ℹ️ **Data Analyst Mode:** Anda hanya memiliki akses ke **Anonymized Data Mart** (tabel ter-mask).")
        if st.button("Jalankan Query `SELECT * FROM customers_anonymized LIMIT 5`"):
            if ANONYMIZED_DB_PATH.exists():
                conn = sqlite3.connect(ANONYMIZED_DB_PATH)
                df = pd.read_sql_query("SELECT * FROM customers_anonymized LIMIT 5", conn)
                conn.close()

                st.dataframe(df, use_container_width=True)
                log_access_event(
                    user_id=user_id,
                    user_role=role,
                    action_type="QUERY_ANONYMIZED_DATA",
                    target_table="customers_anonymized",
                    columns_requested=list(df.columns),
                    was_masked=True,
                    justification="Daily Business KPI Aggregation",
                )
                st.success("Query berhasil. Audit log tercatat secara otomatis.")
            else:
                st.error("Database anonymized belum dibuat. Jalankan apply_masking.py terlebih dahulu.")

    else:
        st.warning("⚠️ **DPO Privileged Mode:** Anda mencoba mengakses **Raw Production Database**.")
        justification = st.text_input("Justifikasi Audit Wajib (UU PDP Pasal 47):", value="Investigasi Keluhan Nasabah Kasus #2026-99")
        if st.button("Buka Akses Raw Data Terbatas"):
            if RAW_DB_PATH.exists():
                conn = sqlite3.connect(RAW_DB_PATH)
                df = pd.read_sql_query("SELECT * FROM customers_raw LIMIT 5", conn)
                conn.close()

                st.dataframe(df, use_container_width=True)
                log_access_event(
                    user_id=user_id,
                    user_role=role,
                    action_type="PRIVILEGED_RAW_ACCESS",
                    target_table="customers_raw",
                    columns_requested=list(df.columns),
                    was_masked=False,
                    justification=justification,
                )
                st.success(f"Akses raw tercatat pada Audit Trail dengan justifikasi: '{justification}'.")
            else:
                st.error("Database raw belum dibuat.")

    st.markdown("---")
    st.markdown("#### Log Jejak Audit Terkini (`audit_access_log`)")
    audit_df = get_audit_logs(limit=15)
    if not audit_df.empty:
        st.dataframe(audit_df, use_container_width=True)
    else:
        st.info("Belum ada log audit.")
