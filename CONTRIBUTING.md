# Contributing

This repository is an archived course project. Before attributing work to a team member, changing the license, or publishing project materials, obtain agreement from the original team and preserve verifiable authorship.

## Development checks

Create a Python 3.10+ virtual environment and install `requirements-dev.lock`. Before opening a pull request, run:

```bash
pytest --cov=backend/painter --cov-report=term-missing
python backend/manage.py check
python backend/manage.py makemigrations --check --dry-run
ruff check backend
ruff format --check backend
```

Never commit `.env`, credentials, databases, user uploads, or real personal data. Add schema changes as Django migrations and include tests for behavior changes.
