"""
Custom Presidio Pattern Recognizer for Indonesian National Identification Number (NIK).
Validates 16 digits, valid province codes, and birthdate formatting (including female day + 40).
"""

from typing import List, Optional
from presidio_analyzer import Pattern, PatternRecognizer

VALID_PROVINCES = {
    11, 12, 13, 14, 15, 16, 17, 18, 19, 21,  # Sumatera
    31, 32, 33, 34, 35, 36,                  # Jawa
    51, 52, 53,                              # Bali & Nusa Tenggara
    61, 62, 63, 64, 65,                      # Kalimantan
    71, 72, 73, 74, 75, 76,                  # Sulawesi
    81, 82, 91, 94                           # Maluku & Papua
}


def is_valid_nik_structure(nik: str) -> bool:
    """Verifies length, province code, and realistic day/month fields."""
    if len(nik) != 16 or not nik.isdigit():
        return False

    prov_code = int(nik[:2])
    if prov_code not in VALID_PROVINCES:
        return False

    day = int(nik[6:8])
    month = int(nik[8:10])

    # Day validation: Male: 1-31, Female: 41-71
    if not ((1 <= day <= 31) or (41 <= day <= 71)):
        return False

    # Month validation: 1-12
    if not (1 <= month <= 12):
        return False

    return True


class IndonesianNikRecognizer(PatternRecognizer):
    """Recognizer for detecting 16-digit Indonesian NIK (Nomor Induk Kependudukan)."""

    PATTERNS = [
        Pattern(
            name="nik_regex",
            regex=r"\b[1-9][0-9]{15}\b",
            score=0.75,
        ),
    ]

    CONTEXT = [
        "nik", "ktp", "identitas", "kependudukan", "nomor induk", 
        "no ktp", "no nik", "national id", "citizen id"
    ]

    def __init__(
        self,
        name: str = "IndonesianNikRecognizer",
        supported_language: str = "en",
        supported_entities: Optional[List[str]] = None,
    ):
        supported_entities = supported_entities or ["ID_NIK"]
        super().__init__(
            supported_entity=supported_entities[0],
            name=name,
            supported_language=supported_language,
            patterns=self.PATTERNS,
            context=self.CONTEXT,
        )

    def validate_result(self, pattern_text: str) -> bool:
        """Returns True if the candidate pattern conforms to Indonesian NIK standards."""
        return is_valid_nik_structure(pattern_text)
