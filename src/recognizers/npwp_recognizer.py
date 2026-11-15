"""
Custom Presidio Pattern Recognizer for Indonesian NPWP (Nomor Pokok Wajib Pajak).
Detects 15 or 16 digit formats with or without standard punctuation.
"""

from typing import List, Optional
from presidio_analyzer import Pattern, PatternRecognizer


class IndonesianNpwpRecognizer(PatternRecognizer):
    """Recognizer for detecting Indonesian NPWP."""

    PATTERNS = [
        Pattern(
            name="npwp_punctuated",
            # Example: 01.234.567.8-901.000
            regex=r"\b[0-9]{2}\.[0-9]{3}\.[0-9]{3}\.[0-9]{1}-[0-9]{3}\.[0-9]{3}\b",
            score=0.90,
        ),
        Pattern(
            name="npwp_digits_only",
            regex=r"\b[0-9]{15,16}\b",
            score=0.40,  # Lower base score; requires context to avoid false positives with NIK
        ),
    ]

    CONTEXT = [
        "npwp", "pajak", "nomor pokok wajib pajak", "tax", "faktur", "wajib pajak"
    ]

    def __init__(
        self,
        name: str = "IndonesianNpwpRecognizer",
        supported_language: str = "en",
        supported_entities: Optional[List[str]] = None,
    ):
        supported_entities = supported_entities or ["ID_NPWP"]
        super().__init__(
            supported_entity=supported_entities[0],
            name=name,
            supported_language=supported_language,
            patterns=self.PATTERNS,
            context=self.CONTEXT,
        )
