"""
掌纹识别模型
"""

from .roi_extraction import PalmprintROIExtractor
from .palmprint_model import PalmprintRecognitionModel

__all__ = [
    "PalmprintROIExtractor",
    "PalmprintRecognitionModel",
]
