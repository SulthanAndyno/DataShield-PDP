"""
Custom Indonesian Recognizers for Presidio Analyzer
"""

from src.recognizers.nik_recognizer import IndonesianNikRecognizer
from src.recognizers.phone_recognizer import IndonesianPhoneRecognizer
from src.recognizers.npwp_recognizer import IndonesianNpwpRecognizer

__all__ = [
    "IndonesianNikRecognizer",
    "IndonesianPhoneRecognizer",
    "IndonesianNpwpRecognizer",
]
