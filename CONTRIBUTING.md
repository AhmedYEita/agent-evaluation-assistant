# Contributing to Agent Evaluation Infrastructure

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## Development Setup

### Prerequisites

- Python 3.12+
- Terraform 1.5+
- GCP account with project access
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

### Pre-Commit Quality Checks

Before committing, run these checks locally:

```bash
# From repository root
cd sdk

# Format code
black agent_evaluation_sdk/

# Lint code
ruff check agent_evaluation_sdk/

# Type check
mypy agent_evaluation_sdk/

# Run tests
pytest

# Validate Terraform (from terraform/)
cd ../terraform
terraform fmt -recursive
terraform init -backend=false
terraform validate
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
│   │   └── dataset/
│   └── main.tf
├── examples/                    # Usage examples
│   └── simple_adk_agent/       # Working demo agent
└── .github/workflows/           # CI/CD pipelines
    ├── test-sdk.yml            # SDK testing & quality checks
    └── validate-infra.yml      # Terraform & infrastructure validation
```

## Making Changes

### Branching Strategy

- `main` - Production-ready code
- `feat/*` - New features
- `fix/*` - Bug fixes
- `docs/*` - Documentation updates

### Development Workflow

1. **Create a branch**
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. **Make changes**
   - Write code
   - Add tests
   - Update documentation

3. **Test locally** (before committing)
   ```bash
   cd sdk
   black agent_evaluation_sdk/
   ruff check agent_evaluation_sdk/
   mypy agent_evaluation_sdk/
   pytest
   ```

4. **Commit changes**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

5. **Push and create PR**
   ```bash
   git push origin feat/your-feature-name
   # Then create PR on GitHub targeting main branch
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
        project_id="test-project-id",
        agent_name="test-agent"
    )
    
    # Assert
    assert wrapper is not None
    assert wrapper.config.project_id == "test-project-id"
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

- Update README.md when adding features
- Add examples for new functionality
- Update DEPLOYMENT_GUIDE.md if deployment process changes

## Pull Request Process

1. **Before submitting:**
   - ✅ All tests pass locally
   - ✅ Code is formatted with `black`
   - ✅ No linting errors from `ruff`
   - ✅ Type checking passes with `mypy`
   - ✅ Terraform validates (if infrastructure changes)
   - ✅ Documentation is updated
   - ✅ No merge conflicts with `main`

2. **PR Description should include:**
   - What changed and why
   - How to test the changes
   - Any breaking changes
   - Related issues (if applicable)

3. **CI/CD Checks:**
   - ✅ `test-sdk.yml` - SDK tests, linting, formatting, type checking
   - ✅ `validate-infra.yml` - Terraform validation and SDK compatibility
   
   All checks must pass before merge.

4. **After approval:**
   - Squash and merge (preferred for clean history)
   - Delete feature branch

## Getting Help

- 📖 **Documentation**: Read the documentation
- 💬 **Issues**: Open an issue on GitHub
- 📧 **Questions**: Contact maintainers

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Help others learn and grow

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing! 🎉
