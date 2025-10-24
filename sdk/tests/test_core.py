"""
Unit tests for core evaluation wrapper functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from agent_evaluation_sdk.core import enable_evaluation, EvaluationWrapper
from agent_evaluation_sdk.config import EvaluationConfig


class TestEvaluationWrapper:
    """Tests for EvaluationWrapper class."""
    
    @patch('agent_evaluation_sdk.core.CloudLogger')
    @patch('agent_evaluation_sdk.core.CloudTracer')
    @patch('agent_evaluation_sdk.core.CloudMetrics')
    @patch('agent_evaluation_sdk.core.DatasetCollector')
    def test_wrapper_initialization(
        self, mock_dataset, mock_metrics, mock_tracer, mock_logger
    ):
        """Test that wrapper initializes all components correctly."""
        # Arrange
        mock_agent = Mock()
        mock_agent.generate_content = Mock()
        config = EvaluationConfig.default("test-project", "test-agent")
        
        # Act
        wrapper = EvaluationWrapper(agent=mock_agent, config=config)
        
        # Assert
        assert wrapper.agent == mock_agent
        assert wrapper.config == config
        mock_logger.assert_called_once()
        mock_tracer.assert_called_once()
        mock_metrics.assert_called_once()
        mock_dataset.assert_called_once()
    
    @patch('agent_evaluation_sdk.core.CloudLogger')
    @patch('agent_evaluation_sdk.core.CloudTracer')
    @patch('agent_evaluation_sdk.core.CloudMetrics')
    @patch('agent_evaluation_sdk.core.DatasetCollector')
    def test_agent_method_wrapping(
        self, mock_dataset, mock_metrics, mock_tracer, mock_logger
    ):
        """Test that agent methods are wrapped correctly."""
        # Arrange
        mock_agent = Mock()
        original_generate = Mock(return_value="test response")
        mock_agent.generate_content = original_generate
        config = EvaluationConfig.default("test-project", "test-agent")
        
        # Act
        wrapper = EvaluationWrapper(agent=mock_agent, config=config)
        
        # Assert - method should be replaced
        assert mock_agent.generate_content != original_generate


class TestEnableEvaluation:
    """Tests for enable_evaluation function."""
    
    @patch('agent_evaluation_sdk.core.EvaluationWrapper')
    def test_enable_evaluation_basic(self, mock_wrapper_class):
        """Test basic enable_evaluation call."""
        # Arrange
        mock_agent = Mock()
        mock_wrapper = Mock()
        mock_wrapper_class.return_value = mock_wrapper
        
        # Act
        result = enable_evaluation(
            agent=mock_agent,
            project_id="test-project",
            agent_name="test-agent"
        )
        
        # Assert
        assert result == mock_wrapper
        mock_wrapper_class.assert_called_once()
    
    @patch('agent_evaluation_sdk.core.EvaluationWrapper')
    @patch('agent_evaluation_sdk.core.EvaluationConfig')
    def test_enable_evaluation_with_config(self, mock_config_class, mock_wrapper_class):
        """Test enable_evaluation with config file."""
        # Arrange
        mock_agent = Mock()
        mock_config = Mock()
        mock_config_class.from_yaml.return_value = mock_config
        
        # Act
        enable_evaluation(
            agent=mock_agent,
            project_id="test-project",
            agent_name="test-agent",
            config_path="test_config.yaml"
        )
        
        # Assert
        mock_config_class.from_yaml.assert_called_once()


class TestExtractMethods:
    """Tests for output and metadata extraction methods."""
    
    @patch('agent_evaluation_sdk.core.CloudLogger')
    @patch('agent_evaluation_sdk.core.CloudTracer')
    @patch('agent_evaluation_sdk.core.CloudMetrics')
    @patch('agent_evaluation_sdk.core.DatasetCollector')
    def test_extract_output_string(
        self, mock_dataset, mock_metrics, mock_tracer, mock_logger
    ):
        """Test extracting output from string response."""
        # Arrange
        mock_agent = Mock()
        config = EvaluationConfig.default("test-project", "test-agent")
        wrapper = EvaluationWrapper(agent=mock_agent, config=config)
        
        # Act
        output = wrapper._extract_output("test response")
        
        # Assert
        assert output == "test response"
    
    @patch('agent_evaluation_sdk.core.CloudLogger')
    @patch('agent_evaluation_sdk.core.CloudTracer')
    @patch('agent_evaluation_sdk.core.CloudMetrics')
    @patch('agent_evaluation_sdk.core.DatasetCollector')
    def test_extract_output_with_text_attribute(
        self, mock_dataset, mock_metrics, mock_tracer, mock_logger
    ):
        """Test extracting output from response with .text attribute."""
        # Arrange
        mock_agent = Mock()
        config = EvaluationConfig.default("test-project", "test-agent")
        wrapper = EvaluationWrapper(agent=mock_agent, config=config)
        
        mock_response = Mock()
        mock_response.text = "test response"
        
        # Act
        output = wrapper._extract_output(mock_response)
        
        # Assert
        assert output == "test response"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

