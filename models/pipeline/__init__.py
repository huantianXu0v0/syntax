"""
识别流水线模块
"""

from .serial_pipeline import SerialPipeline
from .parallel_pipeline import ParallelPipeline
from .decision_fusion import DecisionFusion

__all__ = [
    "SerialPipeline",
    "ParallelPipeline",
    "DecisionFusion",
]
