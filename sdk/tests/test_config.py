"""
Unit tests for configuration management.
"""

import pytest
import yaml
from pathlib import Path
from agent_evaluation_sdk.config import (
    EvaluationConfig,
    LoggingConfig,
    TracingConfig,
    MetricsConfig,
    DatasetConfig,
)


class TestEvaluationConfig:
    """Tests for EvaluationConfig class."""
    
    def test_default_config(self):
        """Test creating default configuration."""
        config = EvaluationConfig.default(
            project_id="test-project",
            agent_name="test-agent"
        )
        
        assert config.project_id == "test-project"
        assert config.agent_name == "test-agent"
        assert config.logging.level == "INFO"
        assert config.tracing.enabled is True
        assert config.metrics.enabled is True
        assert config.dataset.auto_collect is False
    
    def test_custom_config(self):
        """Test creating custom configuration."""
        config = EvaluationConfig(
            project_id="test-project",
            agent_name="test-agent",
            logging=LoggingConfig(level="DEBUG"),
            tracing=TracingConfig(sample_rate=0.5),
            dataset=DatasetConfig(auto_collect=True),
        )
        
        assert config.logging.level == "DEBUG"
        assert config.tracing.sample_rate == 0.5
        assert config.dataset.auto_collect is True
    
    def test_from_yaml(self, tmp_path):
        """Test loading configuration from YAML file."""
        # Create temporary YAML file
        config_file = tmp_path / "config.yaml"
        config_data = {
            "project_id": "yaml-project",
            "agent_name": "yaml-agent",
            "logging": {"level": "WARNING"},
            "tracing": {"enabled": False},
            "dataset": {"auto_collect": False},
        }
        
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)
        
        # Load config
        config = EvaluationConfig.from_yaml(config_file)
        
        assert config.project_id == "yaml-project"
        assert config.agent_name == "yaml-agent"
        assert config.logging.level == "WARNING"
        assert config.tracing.enabled is False
        assert config.dataset.auto_collect is False


class TestSubConfigs:
    """Tests for sub-configuration classes."""
    
    def test_logging_config_defaults(self):
        """Test LoggingConfig default values."""
        config = LoggingConfig()
        
        assert config.level == "INFO"
        assert config.include_trajectories is True
        assert config.include_metadata is True
    
    def test_tracing_config_defaults(self):
        """Test TracingConfig default values."""
        config = TracingConfig()
        
        assert config.enabled is True
        assert config.sample_rate == 1.0
    
    def test_metrics_config_defaults(self):
        """Test MetricsConfig default values."""
        config = MetricsConfig()
        
        assert config.enabled is True
        assert config.custom_metrics == []
    
    def test_dataset_config_defaults(self):
        """Test DatasetConfig default values."""
        config = DatasetConfig()
        
        assert config.auto_collect is False
        assert config.storage_location is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

