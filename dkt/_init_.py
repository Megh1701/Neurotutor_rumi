# dkt/__init__.py
"""
Deep Knowledge Tracing (DKT) Module for NeuroTutor
Predicts student mastery using LSTM-based knowledge tracing
"""

from .infer import predict_mastery_dkt
from .model import DKTModel
from .dataset import DKTDataset

__all__ = [
    'predict_mastery_dkt',
    'DKTModel',
    'DKTDataset'
]