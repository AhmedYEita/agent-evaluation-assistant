"""
Tests package initialization.
"""

import pytest


@pytest.fixture
def mock_gcp_credentials(monkeypatch):
    """Mock GCP credentials for testing."""
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "fake-credentials.json")


@pytest.fixture
def sample_project_id():
    """Provide a sample project ID for testing."""
    return "test-project-12345"


@pytest.fixture
def sample_agent_name():
    """Provide a sample agent name for testing."""
    return "test-agent"
