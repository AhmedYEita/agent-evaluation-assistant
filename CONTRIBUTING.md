# Contributing to Agent Evaluation Infrastructure

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## Development Setup

### Prerequisites

- Python 3.10+
- Terraform 1.5+
- GCP account (for testing)
- Git

### Local Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd agent-evaluation-agent

# Set up Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install SDK in development mode
cd sdk
pip install -e ".[dev]"

# Run tests
pytest

# Check code quality
black agent_evaluation_sdk/
ruff check agent_evaluation_sdk/
mypy agent_evaluation_sdk/
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=agent_evaluation_sdk --cov-report=html

# Run specific test file
pytest tests/test_core.py

# Run with verbose output
pytest -v
```

## Project Structure

```
agent-evaluation-agent/
├── sdk/                          # Python SDK
│   ├── agent_evaluation_sdk/
│   │   ├── __init__.py
│   │   ├── core.py              # Main wrapper
│   │   ├── config.py            # Configuration
│   │   ├── logging.py           # Cloud Logging
│   │   ├── tracing.py           # Cloud Trace
│   │   ├── metrics.py           # Cloud Monitoring
│   │   ├── dataset.py           # Dataset collection
│   │   └── cli.py               # CLI tool
│   ├── tests/
│   └── pyproject.toml
├── terraform/                    # Infrastructure
│   ├── modules/
│   │   ├── logging/
│   │   ├── monitoring/
│   │   └── storage/
│   └── main.tf
├── examples/                     # Usage examples
├── docs/                        # Documentation
└── .github/workflows/           # CI/CD
```

## Making Changes

### Branching Strategy

- `main` - Production-ready code
- `develop` - Integration branch
- `feature/*` - New features
- `fix/*` - Bug fixes
- `docs/*` - Documentation updates

### Workflow

1. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes**
   - Write code
   - Add tests
   - Update documentation

3. **Test locally**
   ```bash
   pytest
   black agent_evaluation_sdk/
   ruff check agent_evaluation_sdk/
   ```

4. **Commit changes**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(sdk): add support for custom metrics
fix(tracing): resolve span ID generation issue
docs(readme): update installation instructions
```

## Code Style

### Python

- Follow [PEP 8](https://pep8.org/)
- Use [Black](https://black.readthedocs.io/) for formatting (line length: 100)
- Use [Ruff](https://github.com/astral-sh/ruff) for linting
- Use type hints where appropriate
- Write docstrings for public functions/classes

```python
def example_function(param: str, count: int = 10) -> List[str]:
    """
    Brief description of the function.
    
    Args:
        param: Description of param
        count: Description of count (default: 10)
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When param is empty
    """
    pass
```

### Terraform

- Use consistent formatting: `terraform fmt`
- Add comments for complex logic
- Use variables for configurable values
- Follow naming conventions (snake_case)

## Testing Guidelines

### Unit Tests

- Test all new features
- Maintain >80% code coverage
- Use pytest fixtures for common setup
- Mock external dependencies (GCP services)

```python
def test_enable_evaluation():
    """Test that evaluation wrapper is created correctly."""
    # Arrange
    mock_agent = Mock()
    
    # Act
    wrapper = enable_evaluation(
        agent=mock_agent,
        project_id="test-project",
        agent_name="test-agent"
    )
    
    # Assert
    assert wrapper is not None
    assert wrapper.config.project_id == "test-project"
```

### Integration Tests

- Test against real GCP services (use test project)
- Clean up resources after tests
- Mark as `@pytest.mark.integration`

## Documentation

### Code Documentation

- Add docstrings to all public APIs
- Include examples in docstrings
- Keep documentation up to date

### User Documentation

- Update README when adding features
- Add examples for new functionality
- Keep docs/ directory current

## Pull Request Process

1. **Before submitting:**
   - All tests pass
   - Code is formatted
   - Documentation is updated
   - No merge conflicts

2. **PR Description should include:**
   - What changed
   - Why it changed
   - How to test
   - Screenshots (if UI changes)

3. **Review process:**
   - At least one approval required
   - CI/CD checks must pass
   - Address review comments

4. **After approval:**
   - Squash and merge
   - Delete feature branch

## Release Process

1. Update version in `sdk/pyproject.toml`
2. Update CHANGELOG.md
3. Create git tag: `git tag v0.2.0`
4. Push tag: `git push origin v0.2.0`
5. GitHub Action will create release and publish to PyPI

## Getting Help

- 📖 Read the [documentation](./docs/README.md)
- 💬 Open an [issue](https://github.com/your-repo/issues)
- 📧 Contact maintainers

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Help others learn and grow

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing! 🎉

