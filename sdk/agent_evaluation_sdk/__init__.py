"""
Agent Evaluation SDK

Production-ready evaluation infrastructure for AI agents.
"""

from agent_evaluation_sdk.config import EvaluationConfig
from agent_evaluation_sdk.core import enable_evaluation
from agent_evaluation_sdk.evaluation import GenAIEvaluator
from agent_evaluation_sdk.regression import RegressionTester

__version__ = "0.1.0"
__all__ = [
    "enable_evaluation",
    "EvaluationConfig",
    "GenAIEvaluator",
    "RegressionTester",
]
