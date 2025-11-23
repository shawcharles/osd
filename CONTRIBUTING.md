# Contributing to Optimized Supergeo Design (OSD)

Thank you for your interest in contributing to OSD! This document provides guidelines for contributing to the project.

## How to Contribute

### Reporting Issues

- Use the GitHub issue tracker to report bugs or suggest features
- Check existing issues before creating a new one to avoid duplicates
- Provide a clear description and reproduction steps for bugs
- Include your environment details (OS, Python version, etc.)

### Pull Requests

We welcome pull requests! Please follow these guidelines:

1. **Fork the repository** and create a new branch from `main`
2. **Make your changes** with clear, descriptive commit messages
3. **Add tests** for new functionality
4. **Update documentation** as needed (README, docstrings, etc.)
5. **Run tests** to ensure nothing is broken: `pytest`
6. **Submit a pull request** with a clear description of changes

### Code Style

- Follow PEP 8 for Python code
- Use type hints where appropriate
- Add docstrings to all public functions and classes
- Keep functions focused and modular

### Testing

- Write unit tests for new functionality
- Ensure all tests pass before submitting a PR: `pytest`
- Aim for good test coverage of critical paths

### Commit Messages

Use clear, descriptive commit messages:

```
Add PCA variance preservation tests

- Test that PCA retains 95% variance as specified
- Add edge cases for small datasets
- Update test fixtures
```

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/asd.git
cd asd

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install in development mode with dev dependencies
pip install -e .[dev]

# Run tests
pytest
```

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the community
- Show empathy towards other community members

## Questions?

Feel free to open an issue for questions or discussions. We're here to help!

## License

By contributing, you agree that your contributions will be licensed under the Apache 2.0 License.
