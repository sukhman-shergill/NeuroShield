# Contributing to NeuroShield

Thank you for your interest in contributing to NeuroShield! This document outlines how to set up your development environment and contribute effectively.

---

## Development Setup

### 1. Fork and Clone

```bash
git clone https://github.com/sukhman-shergill/NeuroShield.git
cd NeuroShield
```

### 2. Python Backend

```bash
python -m venv venv
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

### 3. React Frontend

```bash
cd frontend
npm install
cd ..
```

### 4. Verify Setup (Dry Run)

```bash
# Validate the full pipeline without downloading data or training:
python run_pipeline.py --mode train --dry-run
```

---

## Running Tests

```bash
# Python unit tests
python -m pytest tests/ -v

# Frontend TypeScript check
cd frontend && npm run lint

# Full CI simulation
python -m pytest tests/ && cd frontend && npm run build
```

---

## Code Style

### Python
- Follow PEP 8. Maximum line length: 100 characters.
- Every function must have a docstring with `Args:` and `Returns:` sections.
- Use type hints on all function signatures.
- Imports: stdlib → third-party → local (separated by blank lines).

### TypeScript / React
- Use functional components with hooks.
- No `any` types — be explicit.
- Props interfaces must be named `{ComponentName}Props`.

---

## Pull Request Process

1. Create a feature branch: `git checkout -b feature/your-feature-name`
2. Make your changes with clear, atomic commits.
3. Ensure all tests pass: `python -m pytest && cd frontend && npm run build`
4. Update documentation if you changed any behaviour.
5. Open a PR against `main` with a clear description of what and why.

---

## Areas for Contribution

- 📊 **EDA Notebook**: Exploratory data analysis for UNSW-NB15 dataset
- 🔬 **SHAP Integration**: Full SHAP DeepExplainer in `src/explainer.py`
- 📱 **Mobile Dashboard**: Responsive views for the React SOC dashboard
- 🧪 **Test Coverage**: Unit tests for `src/explainer.py` and `api/engine.py`
- 🐳 **Docker**: Production-hardened Docker images with nginx TLS

---

## Reporting Issues

Please use the GitHub issue templates:
- **Bug**: Something is broken or produces incorrect output
- **Feature Request**: A new capability or improvement

Include: Python version, OS, error message, and steps to reproduce.
