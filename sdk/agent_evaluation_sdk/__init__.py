"""
Agent Evaluation SDK.
"""

import shutil
from pathlib import Path

from agent_evaluation_sdk.config import EvaluationConfig, RegressionConfig
from agent_evaluation_sdk.core import enable_evaluation
from agent_evaluation_sdk.evaluation import GenAIEvaluator
from agent_evaluation_sdk.regression import RegressionTester

__version__ = "0.1.0"
__all__ = [
    "enable_evaluation",
    "EvaluationConfig",
    "RegressionConfig",
    "GenAIEvaluator",
    "RegressionTester",
    "create_config_template",
]


def create_config_template(target_path: str = "eval_config.yaml") -> None:
    """Create a template eval_config.yaml file in the specified location.

    Args:
        target_path: Path where the config template should be created (default: eval_config.yaml)
    """
    # Get the template path from the installed package
    template_path = Path(__file__).parent / "templates" / "eval_config.template.yaml"
    target = Path(target_path)

    if target.exists():
        print(f"⚠️  File already exists: {target_path}")
        print("   Use a different path or delete the existing file first.")
        return

    try:
        shutil.copy(template_path, target)
        print(f"✅ Created eval_config.yaml template at: {target_path}")
        print("   Edit this file with your GCP project_id and preferences.")
    except FileNotFoundError:
        print("❌ Template file not found. Please ensure the SDK is properly installed.")
    except Exception as e:
        print(f"❌ Error creating template: {e}")
