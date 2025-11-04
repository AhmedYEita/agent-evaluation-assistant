"""
Configuration management for agent evaluation.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml


@dataclass
class LoggingConfig:
    """Configuration for Cloud Logging."""

    enabled: bool = True
    level: str = "INFO"
    include_trajectories: bool = True


@dataclass
class TracingConfig:
    """Configuration for Cloud Trace."""

    enabled: bool = True


@dataclass
class MetricsConfig:
    """Configuration for Cloud Monitoring."""

    enabled: bool = True


@dataclass
class DatasetConfig:
    """Configuration for dataset collection."""

    auto_collect: bool = False  # Opt-in only
    storage_location: Optional[str] = None  # BigQuery table or GCS bucket


@dataclass
class GenAIEvalConfig:
    """Configuration for Gen AI Evaluation Service."""

    enabled: bool = False  # Opt-in to run evaluations
    metrics: List[str] = field(default_factory=lambda: ["bleu", "rouge"])  # Automated metrics
    model_name: str = "gemini-1.5-flash"  # Model for model-based evaluation
    criteria: List[str] = field(
        default_factory=lambda: [
            "coherence",
            "fluency",
            "safety",
            "groundedness",
            "fulfillment",
        ]
    )  # Pointwise criteria
    thresholds: dict = field(
        default_factory=lambda: {}
    )  # Optional score thresholds for pass/fail (0-1 scale)


@dataclass
class AgentConfig:
    """Configuration for agent initialization."""

    model: str = "gemini-2.0-flash-exp"


@dataclass
class EvaluationConfig:
    """Main configuration for agent evaluation."""

    project_id: str
    agent_name: str
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    tracing: TracingConfig = field(default_factory=TracingConfig)
    metrics: MetricsConfig = field(default_factory=MetricsConfig)
    dataset: DatasetConfig = field(default_factory=DatasetConfig)
    genai_eval: GenAIEvalConfig = field(default_factory=GenAIEvalConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)

    @classmethod
    def from_yaml(cls, path: Path) -> "EvaluationConfig":
        """Load configuration from YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)

        return cls(
            project_id=data.get("project_id", ""),
            agent_name=data.get("agent_name", ""),
            logging=LoggingConfig(**data.get("logging", {})),
            tracing=TracingConfig(**data.get("tracing", {})),
            metrics=MetricsConfig(**data.get("metrics", {})),
            dataset=DatasetConfig(**data.get("dataset", {})),
            genai_eval=GenAIEvalConfig(**data.get("genai_eval", {})),
            agent=AgentConfig(**data.get("agent", {})),
        )

    @classmethod
    def default(cls, project_id: str, agent_name: str) -> "EvaluationConfig":
        """Create default configuration."""
        return cls(
            project_id=project_id,
            agent_name=agent_name,
        )
