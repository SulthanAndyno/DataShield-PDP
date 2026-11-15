"""
Automated PII Discovery and Cataloging Scanner.
Scans raw database tables using Microsoft Presidio and custom Indonesian recognizers.
"""

import logging
import os
import sqlite3
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd

# Suppress tldextract internet lookup warning by setting fallback
os.environ["TLDEXTRACT_FALLBACK"] = "1"
logging.getLogger("tldextract").setLevel(logging.ERROR)

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from src.audit.audit_logger import save_catalog_entry
from src.config import CONFIDENCE_THRESHOLD, RAW_DB_PATH, SCANNER_SAMPLE_SIZE
from src.recognizers import (
    IndonesianNikRecognizer,
    IndonesianNpwpRecognizer,
    IndonesianPhoneRecognizer,
)


def build_analyzer_engine() -> AnalyzerEngine:
    """Builds and configures the Presidio AnalyzerEngine with custom Indonesian recognizers."""
    # Explicitly configure en_core_web_sm for fast, lightweight offline NLP processing
    nlp_configuration = {
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
    }
    provider = NlpEngineProvider(nlp_configuration=nlp_configuration)
    nlp_engine = provider.create_engine()
    analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
    
    # Register Custom Indonesian Recognizers
    analyzer.registry.add_recognizer(IndonesianNikRecognizer())
    analyzer.registry.add_recognizer(IndonesianPhoneRecognizer())
    analyzer.registry.add_recognizer(IndonesianNpwpRecognizer())
    
    return analyzer


def map_entity_to_governance_policy(entity_type: str) -> Tuple[str, str]:
    """
    Maps detected entity type to UU PDP Classification Tier and Recommended Masking Strategy.
    UU PDP Pasal 4 membagi Data Pribadi menjadi:
    1. Spesifik (Sensitif): NIK, data keuangan/pajak, kesehatan, biometric -> Tier: Restricted
    2. Umum: Nama lengkap, jenis kelamin, nomor telepon, email, alamat -> Tier: Confidential
    """
    mapping = {
        "ID_NIK": ("Restricted", "Partial_Mask"),
        "ID_NPWP": ("Restricted", "Partial_Mask"),
        "ID_PHONE_NUMBER": ("Confidential", "Partial_Mask"),
        "PHONE_NUMBER": ("Confidential", "Partial_Mask"),
        "EMAIL_ADDRESS": ("Confidential", "Domain_Preserve_Mask"),
        "PERSON": ("Confidential", "Redaction"),
        "LOCATION": ("Confidential", "Redaction"),
        "DATE_TIME": ("Internal", "None"),
    }
    return mapping.get(entity_type, ("Internal", "None"))


def scan_database_tables() -> List[Dict]:
    """
    Scans all tables and columns in RAW_DB_PATH, detects PII,
    and updates the governance catalog.
    """
    if not RAW_DB_PATH.exists():
        raise FileNotFoundError(f"Raw database not found at {RAW_DB_PATH}. Run generator first!")

    print(f"[*] Initializing Presidio Analyzer Engine...")
    analyzer = build_analyzer_engine()

    conn = sqlite3.connect(RAW_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall() if not row[0].startswith("sqlite_")]

    catalog_findings = []

    print(f"[*] Found {len(tables)} tables to inspect: {tables}")

    for table in tables:
        print(f"\n--- Scanning Table: '{table}' ---")
        df = pd.read_sql_query(f"SELECT * FROM {table} LIMIT {SCANNER_SAMPLE_SIZE}", conn)

        for column in df.columns:
            # Check if column is purely numeric
            if pd.api.types.is_numeric_dtype(df[column]):
                print(f"  [.] Non-PII (Numeric): {column:22} -> Public / Internal")
                continue

            # Sample non-null values
            sample_series = df[column].dropna().astype(str)
            if sample_series.empty:
                continue

            entity_detections = []
            confidence_scores = []

            # Analyze sample values
            for val in sample_series:
                text_val = str(val).strip()
                if not text_val or len(text_val) < 2:
                    continue

                # Pass column name as context to boost accuracy!
                results = analyzer.analyze(
                    text=text_val,
                    language="en",
                    context=[column.replace("_", " "), table.replace("_", " ")],
                )

                for res in results:
                    if res.score >= CONFIDENCE_THRESHOLD:
                        entity_detections.append(res.entity_type)
                        confidence_scores.append(res.score)

            # Determine dominant entity
            if entity_detections:
                counts = Counter(entity_detections)
                dominant_entity, count = counts.most_common(1)[0]
                ratio = count / len(sample_series)

                # If entity appears in at least 25% of sampled rows
                if ratio >= 0.25:
                    avg_score = sum(
                        [s for e, s in zip(entity_detections, confidence_scores) if e == dominant_entity]
                    ) / count
                    tier, strategy = map_entity_to_governance_policy(dominant_entity)
                    sample_masked = f"[PROTECTED_{dominant_entity}]"

                    save_catalog_entry(
                        database_name="ecommerce_raw",
                        table_name=table,
                        column_name=column,
                        detected_entity=dominant_entity,
                        confidence_score=round(avg_score, 3),
                        classification_tier=tier,
                        masking_strategy=strategy,
                        sample_value_masked=sample_masked,
                    )

                    catalog_findings.append({
                        "table": table,
                        "column": column,
                        "entity": dominant_entity,
                        "confidence": round(avg_score, 3),
                        "frequency": f"{ratio * 100:.1f}%",
                        "tier": tier,
                        "strategy": strategy,
                    })
                    print(f"  [!] PII DETECTED: {column:22} -> {dominant_entity:18} (Score: {avg_score:.2f}, Tier: {tier})")
                else:
                    print(f"  [.] Non-PII:      {column:22} -> Public / Internal")
            else:
                print(f"  [.] Non-PII:      {column:22} -> Public / Internal")

    conn.close()

    print("\n" + "=" * 70)
    print(f"[+] Scan Complete! Discovered {len(catalog_findings)} sensitive PII columns.")
    print("=" * 70)
    return catalog_findings


if __name__ == "__main__":
    scan_database_tables()
