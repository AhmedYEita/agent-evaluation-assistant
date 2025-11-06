"""
Integration tests for the SDK (requires GCP access).

These tests actually interact with GCP services and are marked
with @pytest.mark.integration to be run separately.
"""

import os
from unittest.mock import Mock

import pytest

from agent_evaluation_sdk import enable_evaluation


@pytest.mark.integration
@pytest.mark.skipif(
    not os.environ.get("GCP_PROJECT_ID"),
    reason="GCP_PROJECT_ID not set - skipping integration tests"
)
class TestIntegration:
    """Integration tests that interact with real GCP services."""

    def test_enable_evaluation_integration(self):
        """Test enabling evaluation with real GCP services."""
        # This test requires actual GCP credentials and project
        project_id = os.environ.get("GCP_PROJECT_ID")

        # Create a mock agent
        mock_agent = Mock()
        mock_agent.generate_content = Mock(return_value="test response")

        # Enable evaluation
        wrapper = enable_evaluation(
            agent=mock_agent,
            project_id=project_id,
            agent_name="integration-test-agent"
        )

        # Verify wrapper was created
        assert wrapper is not None
        assert wrapper.config.project_id == project_id

        # Test wrapped agent call
        response = mock_agent.generate_content("test input")
        assert response == "test response"

        # Flush any buffered data
        wrapper.flush()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])

