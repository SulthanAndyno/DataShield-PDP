"""
Custom Presidio Pattern Recognizer for Indonesian Mobile Phone Numbers.
Detects formats starting with 08xx or +628xx with length 10 to 14 digits.
"""

from typing import List, Optional
from presidio_analyzer import Pattern, PatternRecognizer


class IndonesianPhoneRecognizer(PatternRecognizer):
    """Recognizer for detecting Indonesian Mobile Phone Numbers."""

    PATTERNS = [
        Pattern(
            name="indonesian_phone_international",
            regex=r"(?:\+62|62)8[1-9][0-9]{7,10}\b",
            score=0.85,
        ),
        Pattern(
            name="indonesian_phone_domestic",
            regex=r"\b08[1-9][0-9]{7,10}\b",
            score=0.80,
        ),
    ]

    CONTEXT = [
        "telepon", "no hp", "nomor hp", "whatsapp", "wa", "ponsel", 
        "kontak", "phone", "mobile", "handphone", "telp"
    ]

    def __init__(
        self,
        name: str = "IndonesianPhoneRecognizer",
        supported_language: str = "en",
        supported_entities: Optional[List[str]] = None,
    ):
        supported_entities = supported_entities or ["ID_PHONE_NUMBER"]
        super().__init__(
            supported_entity=supported_entities[0],
            name=name,
            supported_language=supported_language,
            patterns=self.PATTERNS,
            context=self.CONTEXT,
        )
