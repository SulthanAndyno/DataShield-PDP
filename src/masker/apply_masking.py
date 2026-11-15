"""
Anonymization and Masking Execution Engine.
Applies deterministic pseudonymization (Salted SHA-256), partial masking,
and redaction according to policies registered in the PII Catalog.
"""

import hashlib
import hmac
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any, Optional
import pandas as pd

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.audit.audit_logger import get_pii_catalog, log_access_event
from src.config import ANONYMIZED_DB_PATH, DATASHIELD_SALT_KEY, RAW_DB_PATH


def hash_pseudonym(value: Any, salt: str = DATASHIELD_SALT_KEY) -> str:
    """
    Computes deterministic HMAC-SHA256 salted hash.
    Allows exact joins and distinct counting across datasets without exposing raw identity.
    """
    if pd.isna(value) or value is None:
        return "NULL"
    h = hmac.new(salt.encode("utf-8"), str(value).encode("utf-8"), hashlib.sha256)
    return f"HASH_{h.hexdigest()[:16]}"


def mask_indonesian_nik(nik: str) -> str:
    """Masks 16-digit NIK, keeping area code (first 6) and counter (last 2): 320101********01"""
    if pd.isna(nik) or not str(nik).strip():
        return "NULL"
    s = str(nik).strip()
    if len(s) == 16:
        return f"{s[:6]}********{s[-2:]}"
    elif len(s) > 4:
        return f"{s[:2]}****{s[-2:]}"
    return "****"


def mask_indonesian_phone(phone: str) -> str:
    """Masks phone number, keeping prefix and last 4 digits: 0812****7890"""
    if pd.isna(phone) or not str(phone).strip():
        return "NULL"
    s = str(phone).strip()
    if len(s) >= 8:
        prefix_len = 4 if s.startswith("08") else 5
        return f"{s[:prefix_len]}****{s[-4:]}"
    return "****"


def mask_email(email: str) -> str:
    """Preserves domain for analytics while masking username: b***o@domain.com"""
    if pd.isna(email) or not str(email).strip():
        return "NULL"
    s = str(email).strip()
    if "@" in s:
        user, domain = s.split("@", 1)
        if len(user) <= 2:
            masked_user = user[0] + "***"
        else:
            masked_user = f"{user[0]}***{user[-1]}"
        return f"{masked_user}@{domain}"
    return "[MASKED_EMAIL]"


def mask_value_by_strategy(val: Any, strategy: str, entity_type: str) -> Any:
    """Dispatches transformation logic according to strategy and entity."""
    if pd.isna(val) or val is None:
        return val

    s_val = str(val).strip()

    if strategy == "Salted_Hash":
        return hash_pseudonym(s_val)

    elif strategy == "Partial_Mask":
        if "NIK" in entity_type:
            return mask_indonesian_nik(s_val)
        elif "PHONE" in entity_type:
            return mask_indonesian_phone(s_val)
        elif "NPWP" in entity_type:
            return s_val[:4] + "***-***-***"
        return mask_indonesian_phone(s_val)

    elif strategy == "Domain_Preserve_Mask" or "EMAIL" in entity_type:
        return mask_email(s_val)

    elif strategy == "Redaction":
        if "PERSON" in entity_type:
            return "[CONFIDENTIAL_NAME]"
        elif "LOCATION" in entity_type:
            # Preserve city / province if available, mask detailed street
            parts = s_val.split(",")
            return f"[PROTECTED_STREET], {parts[-1].strip()}" if len(parts) > 1 else "[PROTECTED_ADDRESS]"
        return "[REDACTED]"

    return val


def create_anonymized_data_mart():
    """
    Reads raw database, retrieves catalog masking policies,
    transforms sensitive columns, and writes to ANONYMIZED_DB_PATH.
    """
    if not RAW_DB_PATH.exists():
        raise FileNotFoundError(f"Raw database not found at {RAW_DB_PATH}")

    catalog_df = get_pii_catalog()
    if catalog_df.empty:
        print("[!] Warning: PII Catalog is empty! Run scanner first to discover sensitive columns.")
        return

    # Build policy dictionary: (table_name, column_name) -> (strategy, entity)
    policies = {}
    for _, row in catalog_df.iterrows():
        policies[(row["table_name"], row["column_name"])] = (
            row["masking_strategy"],
            row["detected_entity"],
        )

    print(f"[*] Loaded {len(policies)} masking policies from Governance Catalog.")

    conn_raw = sqlite3.connect(RAW_DB_PATH)
    conn_anon = sqlite3.connect(ANONYMIZED_DB_PATH)

    cursor = conn_raw.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall() if not row[0].startswith("sqlite_")]

    for table in tables:
        print(f"\n[*] Processing Table: '{table}'...")
        df = pd.read_sql_query(f"SELECT * FROM {table}", conn_raw)
        original_cols = list(df.columns)
        masked_cols_applied = []

        # Also pseudonymize primary customer key if present
        if "customer_id" in df.columns:
            df["customer_hash_id"] = df["customer_id"].apply(hash_pseudonym)
            masked_cols_applied.append("customer_id -> customer_hash_id")
            # Drop raw customer_id in anonymized mart for pure safety
            df = df.drop(columns=["customer_id"])

        for col in df.columns:
            key = (table, col)
            if key in policies:
                strat, ent = policies[key]
                print(f"  -> Masking column '{col}' using {strat} ({ent})")
                df[col] = df[col].apply(lambda v: mask_value_by_strategy(v, strat, ent))
                masked_cols_applied.append(col)

        target_table_name = table.replace("_raw", "_anonymized")
        df.to_sql(target_table_name, conn_anon, if_exists="replace", index=False)
        print(f"[+] Materialized table '{target_table_name}' with {len(df)} records in Anonymized Mart.")

        # Save CSV export
        csv_path = ANONYMIZED_DB_PATH.parent / f"{target_table_name}.csv"
        df.to_csv(csv_path, index=False)

        # Log this event in the compliance audit trail
        log_access_event(
            user_id="ETL_ANONYMIZER_SERVICE",
            user_role="System_Automated_Pipeline",
            action_type="PII_MASKING_TRANSFORMATION",
            target_table=table,
            columns_requested=masked_cols_applied,
            was_masked=True,
            justification="Scheduled Anonymization Pipeline for UU PDP Compliance",
        )

    conn_raw.close()
    conn_anon.close()

    print("\n" + "=" * 70)
    print(f"[+] Anonymization Pipeline Complete! Protected Mart created at:\n    {ANONYMIZED_DB_PATH}")
    print("=" * 70)


if __name__ == "__main__":
    create_anonymized_data_mart()
