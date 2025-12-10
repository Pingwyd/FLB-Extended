FLB Extended — Project Skeleton

This repository starts a platform connecting farmers, workers, realtors and service providers.

Purpose
- Capture project concept and provide a minimal runnable prototype (Flask + SQLAlchemy).

What's included
- app.py — minimal Flask application and DB init
- models.py — core SQLAlchemy models (User example)
- config.py — basic configuration (SQLite for quick start)
- requirements.txt — Python dependencies
- tests/test_app.py — small pytest to validate the health endpoint

How to run (Windows PowerShell)

# Install dependencies into the active Python environment
python -m pip install -r requirements.txt

# Run the app
python app.py

# Run tests
python -m pytest -q

Next steps
- Expand models (Account types, Verification, Messaging, Contracts)
- Add authentication, payment integration, and front-end
- Add migrations and production config
