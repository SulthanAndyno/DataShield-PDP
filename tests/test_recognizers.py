"""
Unit tests for Custom Indonesian Presidio Recognizers (NIK, Phone, NPWP).
"""

import sys
from pathlib import Path
import pytest

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.recognizers.nik_recognizer import (
    IndonesianNikRecognizer,
    is_valid_nik_structure,
)
from src.recognizers.npwp_recognizer import IndonesianNpwpRecognizer
from src.recognizers.phone_recognizer import IndonesianPhoneRecognizer
from src.scanner.run_scanner import build_analyzer_engine


class TestIndonesianRecognizers:

    def test_nik_structure_validator(self):
        # Valid: Prov 32 (Jabar), Day 12, Month 05, Year 98, Serial 0001
        valid_nik_male = "3201011205980001"
        assert is_valid_nik_structure(valid_nik_male) is True

        # Valid: Prov 31 (DKI), Female Day (12 + 40 = 52), Month 08
        valid_nik_female = "3171015208950002"
        assert is_valid_nik_structure(valid_nik_female) is True

        # Invalid: 15 digits
        assert is_valid_nik_structure("320101120598000") is False

        # Invalid: Non-existent province code (99)
        assert is_valid_nik_structure("9901011205980001") is False

        # Invalid: Month 13
        assert is_valid_nik_structure("3201011213980001") is False

    def test_nik_presidio_analysis(self):
        analyzer = build_analyzer_engine()
        text = "Nasabah memiliki KTP dengan NIK 3201011205980001 di Bandung."
        results = analyzer.analyze(text=text, language="en")
        
        nik_results = [r for r in results if r.entity_type == "ID_NIK"]
        assert len(nik_results) == 1
        assert nik_results[0].score >= 0.75
        matched_text = text[nik_results[0].start : nik_results[0].end]
        assert matched_text == "3201011205980001"

    def test_phone_presidio_analysis(self):
        analyzer = build_analyzer_engine()
        text_domestic = "Kontak WhatsApp customer: 081234567890."
        results = analyzer.analyze(text=text_domestic, language="en")
        phone_results = [r for r in results if r.entity_type == "ID_PHONE_NUMBER"]
        assert len(phone_results) == 1

        text_intl = "Telepon kantor: +6281398765432."
        results_intl = analyzer.analyze(text=text_intl, language="en")
        phone_intl = [r for r in results_intl if r.entity_type == "ID_PHONE_NUMBER"]
        assert len(phone_intl) == 1

    def test_npwp_presidio_analysis(self):
        analyzer = build_analyzer_engine()
        text = "Faktur pajak dengan NPWP 01.345.678.9-012.000 atas nama PT Contoh."
        results = analyzer.analyze(text=text, language="en")
        npwp_results = [r for r in results if r.entity_type == "ID_NPWP"]
        assert len(npwp_results) == 1
