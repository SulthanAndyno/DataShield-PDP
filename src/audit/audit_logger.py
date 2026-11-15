"""
Audit Logging and Metadata Management Module.
Maintains the PII Data Catalog and immutable access logs for UU PDP compliance verification.
"""

import sqlite3
import uuid
from datetime import datetime
from typing import List, Optional
import pandas as pd
from src.config import METADATA_DB_PATH


def init_metadata_db():
    """Initializes SQLite tables for pii_catalog and audit_access_log."""
    METADATA_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(METADATA_DB_PATH)
    cursor = conn.cursor()

    # 1. PII Catalog Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pii_catalog (
        catalog_id TEXT PRIMARY KEY,
        database_name TEXT NOT NULL,
        table_name TEXT NOT NULL,
        column_name TEXT NOT NULL,
        detected_entity TEXT NOT NULL,
        confidence_score REAL NOT NULL,
        classification_tier TEXT NOT NULL,
        masking_strategy TEXT NOT NULL,
        sample_value_masked TEXT,
        is_compliant INTEGER NOT NULL DEFAULT 1,
        scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(database_name, table_name, column_name)
    );
    """)

    # 2. Audit Access Log Table (Immutable)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_access_log (
        event_id TEXT PRIMARY KEY,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        user_id TEXT NOT NULL,
        user_role TEXT NOT NULL,
        action_type TEXT NOT NULL,
        target_table TEXT NOT NULL,
        columns_requested TEXT NOT NULL,
        was_masked INTEGER NOT NULL,
        justification TEXT
    );
    """)

    conn.commit()
    conn.close()


def log_access_event(
    user_id: str,
    user_role: str,
    action_type: str,
    target_table: str,
    columns_requested: List[str],
    was_masked: bool,
    justification: Optional[str] = "Standard analytical operations",
):
    """Records an access event into the immutable audit trail."""
    init_metadata_db()
    conn = sqlite3.connect(METADATA_DB_PATH)
    cursor = conn.cursor()

    event_id = f"EVT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
    cols_str = ", ".join(columns_requested)

    cursor.execute(
        """
        INSERT INTO audit_access_log 
        (event_id, user_id, user_role, action_type, target_table, columns_requested, was_masked, justification)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event_id,
            user_id,
            user_role,
            action_type,
            target_table,
            cols_str,
            1 if was_masked else 0,
            justification,
        ),
    )
    conn.commit()
    conn.close()
    return event_id


def save_catalog_entry(
    database_name: str,
    table_name: str,
    column_name: str,
    detected_entity: str,
    confidence_score: float,
    classification_tier: str,
    masking_strategy: str,
    sample_value_masked: str,
):
    """Saves or updates a column classification record in the catalog."""
    init_metadata_db()
    conn = sqlite3.connect(METADATA_DB_PATH)
    cursor = conn.cursor()

    catalog_id = f"CAT-{uuid.uuid4().hex[:8]}"

    cursor.execute(
        """
        INSERT INTO pii_catalog
        (catalog_id, database_name, table_name, column_name, detected_entity, 
         confidence_score, classification_tier, masking_strategy, sample_value_masked, is_compliant, scanned_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
        ON CONFLICT(database_name, table_name, column_name) DO UPDATE SET
            detected_entity=excluded.detected_entity,
            confidence_score=excluded.confidence_score,
            classification_tier=excluded.classification_tier,
            masking_strategy=excluded.masking_strategy,
            sample_value_masked=excluded.sample_value_masked,
            scanned_at=CURRENT_TIMESTAMP
        """,
        (
            catalog_id,
            database_name,
            table_name,
            column_name,
            detected_entity,
            confidence_score,
            classification_tier,
            masking_strategy,
            sample_value_masked,
        ),
    )
    conn.commit()
    conn.close()


def get_pii_catalog() -> pd.DataFrame:
    """Retrieves all discovered PII catalog items as a DataFrame."""
    init_metadata_db()
    conn = sqlite3.connect(METADATA_DB_PATH)
    df = pd.read_sql_query("SELECT * FROM pii_catalog ORDER BY table_name, column_name", conn)
    conn.close()
    return df


def get_audit_logs(limit: int = 50) -> pd.DataFrame:
    """Retrieves the recent audit trail logs."""
    init_metadata_db()
    conn = sqlite3.connect(METADATA_DB_PATH)
    df = pd.read_sql_query(
        f"SELECT * FROM audit_access_log ORDER BY timestamp DESC LIMIT {limit}", conn
    )
    conn.close()
    return df


if __name__ == "__main__":
    init_metadata_db()
    print("[+] Audit & Metadata DB successfully initialized at:", METADATA_DB_PATH)
