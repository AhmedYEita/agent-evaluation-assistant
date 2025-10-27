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

    level: str = "INFO"
    include_trajectories: bool = True
    include_metadata: bool = True


@dataclass
class TracingConfig:
    """Configuration for Cloud Trace."""

    enabled: bool = True
    sample_rate: float = 1.0  # Trace 100% of requests by default


@dataclass
class MetricsConfig:
    """Configuration for Cloud Monitoring."""

    enabled: bool = True
    custom_metrics: List[str] = field(default_factory=list)


@dataclass
class DatasetConfig:
    """Configuration for dataset collection."""

    auto_collect: bool = True
    sample_rate: float = 0.1  # Collect 10% of interactions
    storage_location: Optional[str] = None  # BigQuery table or GCS bucket


@dataclass
class EvaluationConfig:
    """Main configuration for agent evaluation."""

    project_id: str
    agent_name: str
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    tracing: TracingConfig = field(default_factory=TracingConfig)
    metrics: MetricsConfig = field(default_factory=MetricsConfig)
    dataset: DatasetConfig = field(default_factory=DatasetConfig)

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
        )

    @classmethod
    def default(cls, project_id: str, agent_name: str) -> "EvaluationConfig":
        """Create default configuration."""
        return cls(
            project_id=project_id,
            agent_name=agent_name,
        )

