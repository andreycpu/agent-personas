# Contributing to Agent Personas

Thank you for your interest in contributing to the Agent Personas framework! This guide will help you get started with contributing to the project.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [How Can I Contribute?](#how-can-i-contribute)
3. [Development Setup](#development-setup)
4. [Coding Standards](#coding-standards)
5. [Testing Guidelines](#testing-guidelines)
6. [Documentation](#documentation)
7. [Pull Request Process](#pull-request-process)
8. [Issue Reporting](#issue-reporting)
9. [Security Issues](#security-issues)

## Code of Conduct

This project adheres to a code of conduct that we expect all contributors to follow. Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md) to ensure a welcoming environment for everyone.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the [existing issues](https://github.com/andreycpu/agent-personas/issues) to see if the problem has already been reported. When you are creating a bug report, please include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples to demonstrate the steps**
- **Describe the behavior you observed after following the steps**
- **Explain which behavior you expected to see instead and why**
- **Include screenshots if applicable**
- **Include your environment details** (OS, Python version, package version)

### Suggesting Enhancements

Enhancement suggestions are welcome! Please provide:

- **A clear and descriptive title**
- **A detailed description of the suggested enhancement**
- **Explain why this enhancement would be useful**
- **List any similar features in other tools/libraries**
- **Include mockups or examples if applicable**

### Contributing Code

We welcome code contributions! Here are the types of contributions we're looking for:

- **Bug fixes**
- **New features**
- **Performance improvements**
- **Code refactoring**
- **Documentation improvements**
- **Test coverage improvements**

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Git
- A virtual environment manager (virtualenv, conda, etc.)

### Setting Up the Development Environment

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/agent-personas.git
   cd agent-personas
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install the package in development mode:**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Install pre-commit hooks:**
   ```bash
   pre-commit install
   ```

5. **Verify the setup:**
   ```bash
   python -c "import agent_personas; print('Setup successful!')"
   pytest tests/ -v
   ```

### Development Workflow

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-description
   ```

2. **Make your changes**

3. **Run tests and linting:**
   ```bash
   # Run tests
   pytest tests/ -v --cov=agent_personas
   
   # Run linting
   black agent_personas/ tests/ examples/
   flake8 agent_personas/ tests/ examples/
   mypy agent_personas/
   
   # Run security scan
   bandit -r agent_personas/
   ```

4. **Commit your changes:**
   ```bash
   git add .
   git commit -m "Add: descriptive commit message"
   ```

5. **Push and create a pull request:**
   ```bash
   git push origin feature/your-feature-name
   ```

## Coding Standards

### Code Style

We use several tools to maintain code quality:

- **Black** for code formatting
- **flake8** for linting
- **mypy** for type checking
- **isort** for import sorting

### Python Style Guidelines

1. **Follow PEP 8** with these modifications:
   - Line length: 88 characters (Black default)
   - Use double quotes for strings
   - Use trailing commas in multi-line constructs

2. **Type hints are required** for all public APIs:
   ```python
   def process_persona(persona: Persona) -> Dict[str, Any]:
       """Process a persona and return metadata."""
       return {"name": persona.name, "traits": len(persona.traits)}
   ```

3. **Use descriptive variable and function names:**
   ```python
   # Good
   def calculate_trait_average(traits: Dict[str, float]) -> float:
       return sum(traits.values()) / len(traits)
   
   # Bad
   def calc(t: dict) -> float:
       return sum(t.values()) / len(t)
   ```

4. **Include comprehensive docstrings:**
   ```python
   def create_persona_from_template(
       template_name: str, 
       customizations: Optional[Dict[str, Any]] = None
   ) -> Persona:
       """
       Create a persona from a predefined template.
       
       Args:
           template_name: Name of the template to use
           customizations: Optional trait overrides and customizations
           
       Returns:
           A new Persona instance based on the template
           
       Raises:
           TemplateNotFoundError: If the template doesn't exist
           PersonaValidationError: If the resulting persona is invalid
           
       Example:
           >>> persona = create_persona_from_template(
           ...     "helpful_assistant",
           ...     {"helpfulness": 0.95}
           ... )
           >>> print(persona.name)
           helpful_assistant
       """
   ```

### Error Handling

1. **Use specific exception types:**
   ```python
   # Good
   if not isinstance(persona, Persona):
       raise PersonaValidationError(f"Expected Persona, got {type(persona)}")
   
   # Bad
   if not isinstance(persona, Persona):
       raise ValueError("Wrong type")
   ```

2. **Include context in error messages:**
   ```python
   try:
       persona.validate()
   except PersonaValidationError as e:
       logger.error(f"Failed to validate persona '{persona.name}': {e}")
       raise PersonaManagerError(f"Persona validation failed: {e}") from e
   ```

3. **Log appropriately:**
   ```python
   import logging
   
   logger = logging.getLogger(__name__)
   
   def risky_operation():
       try:
           # ... operation code ...
           logger.debug("Operation completed successfully")
       except SpecificError as e:
           logger.error(f"Operation failed: {e}")
           raise
       except Exception as e:
           logger.critical(f"Unexpected error: {e}")
           raise
   ```

## Testing Guidelines

### Test Structure

Tests are organized in the `tests/` directory, mirroring the package structure:

```
tests/
├── __init__.py
├── test_core_persona.py
├── test_core_manager.py
├── test_core_registry.py
├── test_cache_memory.py
├── test_config_validators.py
├── test_utils_helpers.py
└── fixtures/
    ├── personas.json
    └── configurations.yaml
```

### Writing Tests

1. **Use descriptive test names:**
   ```python
   def test_persona_creation_with_valid_traits():
       """Test that personas are created correctly with valid trait values."""
   
   def test_persona_validation_fails_with_invalid_trait_values():
       """Test that persona validation fails when trait values are out of range."""
   ```

2. **Follow the AAA pattern** (Arrange, Act, Assert):
   ```python
   def test_persona_trait_modification():
       # Arrange
       persona = Persona(name="test", traits={"creativity": 0.5})
       
       # Act
       persona.set_trait("creativity", 0.8)
       
       # Assert
       assert persona.get_trait("creativity") == 0.8
   ```

3. **Test edge cases and error conditions:**
   ```python
   def test_set_trait_with_invalid_value_raises_error():
       persona = Persona(name="test")
       
       with pytest.raises(PersonaValidationError):
           persona.set_trait("invalid", 1.5)  # Value > 1.0
   
   def test_empty_persona_name_raises_error():
       with pytest.raises(PersonaValidationError):
           Persona(name="")
   ```

4. **Use fixtures for common test data:**
   ```python
   @pytest.fixture
   def sample_persona():
       return Persona(
           name="test_persona",
           description="A test persona",
           traits={"creativity": 0.8, "logic": 0.6}
       )
   
   def test_persona_to_dict(sample_persona):
       data = sample_persona.to_dict()
       assert data["name"] == "test_persona"
       assert data["traits"]["creativity"] == 0.8
   ```

### Test Coverage

- Aim for **90%+ test coverage**
- All public APIs must be tested
- Include both positive and negative test cases
- Test error conditions and edge cases

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=agent_personas --cov-report=html

# Run specific test file
pytest tests/test_core_persona.py

# Run tests with specific marker
pytest -m "not slow"

# Run tests in verbose mode
pytest -v
```

## Documentation

### Code Documentation

1. **All public functions and classes** must have docstrings
2. **Use Google-style docstrings:**
   ```python
   def complex_function(param1: str, param2: int = 10) -> Tuple[bool, str]:
       """
       Brief description of what the function does.
       
       Longer description if necessary, explaining the algorithm,
       assumptions, or important details.
       
       Args:
           param1: Description of the first parameter.
           param2: Description of the second parameter. Defaults to 10.
           
       Returns:
           A tuple containing:
           - bool: Success status
           - str: Result message or error description
           
       Raises:
           ValueError: If param1 is empty.
           TypeError: If param2 is not an integer.
           
       Example:
           >>> success, message = complex_function("test", 20)
           >>> print(f"Success: {success}, Message: {message}")
           Success: True, Message: Operation completed
       """
   ```

3. **Include type hints** for all parameters and return values

### User Documentation

1. **Update relevant documentation** when adding features
2. **Include examples** in the user guide
3. **Update the API reference** for new public APIs

### Building Documentation

```bash
# Install documentation dependencies
pip install -e ".[docs]"

# Build HTML documentation
cd docs/
make html

# View documentation
open _build/html/index.html
```

## Pull Request Process

### Before Submitting

1. **Ensure all tests pass:**
   ```bash
   pytest tests/ --cov=agent_personas
   ```

2. **Run the full linting suite:**
   ```bash
   black agent_personas/ tests/ examples/
   flake8 agent_personas/ tests/ examples/
   mypy agent_personas/
   bandit -r agent_personas/
   ```

3. **Update documentation** if necessary

4. **Add tests** for new functionality

### Pull Request Guidelines

1. **Use a descriptive title** and follow conventional commits:
   - `feat: add new persona validation features`
   - `fix: resolve trait caching issue`
   - `docs: update user guide with examples`
   - `test: add coverage for edge cases`

2. **Fill out the PR template** completely

3. **Keep PRs focused** - one feature/fix per PR

4. **Include screenshots** for UI changes

5. **Reference related issues:**
   - `Fixes #123`
   - `Closes #456`
   - `Related to #789`

### PR Review Process

1. **Automated checks** must pass (CI/CD pipeline)
2. **At least one maintainer** must approve
3. **All conversations** must be resolved
4. **Squash merge** is preferred for feature branches

## Issue Reporting

### Bug Reports

Use the bug report template and include:

- **Environment information**
- **Steps to reproduce**
- **Expected vs actual behavior**
- **Code samples** or error messages
- **Screenshots** if applicable

### Feature Requests

Use the feature request template and include:

- **Clear description** of the feature
- **Use case** and motivation
- **Proposed API** or interface
- **Alternative solutions** considered

### Issue Labels

- `bug` - Something isn't working
- `enhancement` - New feature or request
- `documentation` - Improvements or additions to documentation
- `good first issue` - Good for newcomers
- `help wanted` - Extra attention is needed
- `question` - Further information is requested

## Security Issues

**Do not report security issues publicly.** Instead:

1. Email security@example.com with details
2. Include "SECURITY" in the subject line
3. Provide a detailed description
4. Allow time for assessment and patching

## Development Tools

### Recommended IDE Settings

#### VS Code
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"],
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true
    }
}
```

### Git Hooks

Pre-commit hooks are configured to run:
- Black (formatting)
- isort (import sorting)
- flake8 (linting)
- mypy (type checking)
- bandit (security scanning)

## Getting Help

- **Documentation:** Check the [user guide](docs/user_guide.md) and [API reference](docs/api_reference.md)
- **Issues:** Search [existing issues](https://github.com/andreycpu/agent-personas/issues)
- **Discussions:** Use [GitHub Discussions](https://github.com/andreycpu/agent-personas/discussions)
- **Email:** Contact the maintainers at dev@example.com

## Recognition

Contributors will be acknowledged in:
- The CONTRIBUTORS.md file
- Release notes for significant contributions
- The project's README

Thank you for contributing to Agent Personas! 🎭