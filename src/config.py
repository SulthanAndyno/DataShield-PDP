"""
Configuration module for DataShield-PDP.
Loads environment variables and sets up project-wide paths and security keys.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory: /workspace/Projects/DataShield-PDP
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

# Cryptographic Salt Key
DATASHIELD_SALT_KEY = os.getenv(
    "DATASHIELD_SALT_KEY", "default-insecure-dev-salt-key-2026"
)

# Database & Storage Paths
RAW_DB_PATH = BASE_DIR / os.getenv("RAW_DB_PATH", "data/raw/ecommerce_raw.db")
ANONYMIZED_DB_PATH = BASE_DIR / os.getenv(
    "ANONYMIZED_DB_PATH", "data/anonymized/ecommerce_anonymized.db"
)
METADATA_DB_PATH = BASE_DIR / os.getenv(
    "METADATA_DB_PATH", "data/metadata/governance_catalog.db"
)

# Scanner Settings
SCANNER_SAMPLE_SIZE = int(os.getenv("SCANNER_SAMPLE_SIZE", "200"))
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.60"))

# Ensure data directories exist
RAW_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
ANONYMIZED_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
METADATA_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
