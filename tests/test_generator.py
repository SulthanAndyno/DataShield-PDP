"""
Unit tests for Synthetic Data Generator.
"""

import sys
from pathlib import Path
import pytest

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.generator.generate_mock_data import (
    generate_indonesian_nik,
    generate_indonesian_npwp,
    generate_indonesian_phone,
    generate_mock_dataset,
)
from src.recognizers.nik_recognizer import is_valid_nik_structure


class TestSyntheticGenerator:

    def test_synthetic_nik_generation(self):
        for _ in range(50):
            nik = generate_indonesian_nik()
            assert len(nik) == 16
            assert nik.isdigit()
            assert is_valid_nik_structure(nik) is True

    def test_synthetic_npwp_generation(self):
        for _ in range(20):
            npwp = generate_indonesian_npwp()
            assert len(npwp) == 20
            assert "." in npwp and "-" in npwp

    def test_synthetic_phone_generation(self):
        for _ in range(20):
            phone = generate_indonesian_phone()
            assert phone.startswith("08") or phone.startswith("+628")
            assert len(phone) >= 10
