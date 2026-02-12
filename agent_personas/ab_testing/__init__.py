"""
A/B Testing Framework for Personas

Comprehensive testing framework for comparing persona performance,
conducting experiments, and optimizing persona characteristics.
"""

from .experiment_designer import ExperimentDesigner, Experiment, ExperimentType
from .test_runner import TestRunner, TestSession
from .statistical_analyzer import StatisticalAnalyzer, TestResult
from .performance_tracker import PerformanceTracker, Metric
from .experiment_manager import ExperimentManager

__all__ = [
    "ExperimentDesigner",
    "Experiment", 
    "ExperimentType",
    "TestRunner",
    "TestSession",
    "StatisticalAnalyzer",
    "TestResult",
    "PerformanceTracker",
    "Metric",
    "ExperimentManager"
]