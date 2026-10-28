"""Small helpers for the optional Groq connection used by both policy agents."""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # The app can still run if python-dotenv is not installed.
    load_dotenv = None


def get_groq_client():
    """Load local settings and return a Groq client, or None when it is off."""
    # I keep credentials in .env instead of putting a secret directly in Python.
    if load_dotenv:
        project_root = Path(__file__).resolve().parents[1]
        load_dotenv(project_root / ".env", override=False)

    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key or api_key.lower() in {"put_your_key_here", "your_groq_api_key_here"}:
        return None

    try:
        from groq import Groq
    except ImportError:
        return None

    # The model can be changed in .env if Groq changes its available models.
    return Groq(api_key=api_key, timeout=20.0, max_retries=1)


def get_groq_model():
    """Use the configured model name, with a sensible default for this project."""
    if load_dotenv:
        project_root = Path(__file__).resolve().parents[1]
        load_dotenv(project_root / ".env", override=False)
    return os.getenv("GROQ_MODEL", "openai/gpt-oss-120b").strip()
