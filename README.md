# VehicleWise

A vehicle comparison and recommendation platform built with Python, Streamlit, FastAPI and SQLite.

## Features
- Vehicle exploration and filtering
- Vehicle comparison
- Vehicle catalogue
- Personalised recommendations
- User registration and authentication
- Saved comparisons and bookmarks

## Installation

Requirements: Python 3.13 or compatible, Git.

```bash
git clone https://github.com/jayanthkumar-cyber03/vehiclewise.git
cd vehiclewise
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Generate a new secret key and put it in SECRET_KEY in your .env file:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Run the application

Start the backend in one terminal:

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Start the frontend in another terminal:

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

## Tests

```bash
python -m pytest -q
```

## Security

Never commit .env, credentials, passwords or local database files.
