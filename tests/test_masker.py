"""
Unit tests for Masking Engine and Cryptographic Salted Hashing.
"""

import sys
from pathlib import Path
import pytest

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.masker.apply_masking import (
    hash_pseudonym,
    mask_email,
    mask_indonesian_nik,
    mask_indonesian_phone,
    mask_value_by_strategy,
)


class TestMaskingEngine:

    def test_nik_masking(self):
        nik = "3201011205980001"
        masked = mask_indonesian_nik(nik)
        # Keeps first 6 and last 2, masks middle 8 with *
        assert masked == "320101********01"
        assert len(masked) == 16
        assert masked.startswith("320101")
        assert masked.endswith("01")

    def test_phone_masking(self):
        phone_domestic = "081234567890"
        masked_dom = mask_indonesian_phone(phone_domestic)
        assert masked_dom == "0812****7890"

        phone_intl = "+6281234567890"
        masked_intl = mask_indonesian_phone(phone_intl)
        assert masked_intl == "+6281****7890"

    def test_email_masking(self):
        email = "budi.santoso@gmail.com"
        masked = mask_email(email)
        assert masked.endswith("@gmail.com")
        assert masked.startswith("b***")

    def test_salted_hashing_determinism_and_security(self):
        customer_id_1 = "CUST-UUID-1234-5678"
        customer_id_2 = "CUST-UUID-9999-8888"
        salt = "test-salt-secret-key"

        # Deterministic: Same ID and same salt must yield identical hash
        hash_1a = hash_pseudonym(customer_id_1, salt=salt)
        hash_1b = hash_pseudonym(customer_id_1, salt=salt)
        assert hash_1a == hash_1b
        assert hash_1a.startswith("HASH_")

        # Distinct: Different IDs must yield different hashes
        hash_2 = hash_pseudonym(customer_id_2, salt=salt)
        assert hash_1a != hash_2

        # Salt Sensitivity: Different salt must yield different hash
        hash_1_diff_salt = hash_pseudonym(customer_id_1, salt="other-salt")
        assert hash_1a != hash_1_diff_salt

    def test_strategy_dispatcher(self):
        assert mask_value_by_strategy("3201011205980001", "Partial_Mask", "ID_NIK") == "320101********01"
        assert mask_value_by_strategy("Budi Santoso", "Redaction", "PERSON") == "[CONFIDENTIAL_NAME]"
        assert mask_value_by_strategy(1000000, "None", "DATE_TIME") == 1000000
