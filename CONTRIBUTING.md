# Contributing to NutriLens AI

Thank you for your interest in contributing! This guide will help you get started.

## Development Setup

1. Fork and clone the repository
2. Copy `.env.example` to `.env` and fill in your API keys
3. Install Python dependencies: `pip install -r requirements.txt`
4. Run the server: `uvicorn main:app --reload --port 8000`
5. Run tests: `pytest --cov=app -v`

## Code Standards

- **Python**: PEP 8 with type hints, docstrings on all public functions
- **Pydantic v2**: All API schemas use BaseModel with Field validators
- **Services**: Each service file starts with a module docstring (Purpose, Input, Output, Deps)
- **Tests**: Every endpoint has at least 2 tests (success + validation failure)

## Pull Request Process

1. Create a feature branch from `main`
2. Write tests for any new functionality
3. Ensure all tests pass: `pytest -v`
4. Update README if adding new features or services
5. Submit PR with a clear description of changes

## Commit Messages

Use conventional commits: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`

## Code of Conduct

Be kind, constructive, and respectful. We're building something that helps people eat better — let's be a team that works well together.
