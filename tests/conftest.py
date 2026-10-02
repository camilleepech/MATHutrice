"""Make the Project importable with no `.env`, as in CI.

This runs before the first import of the Project: `load_dotenv` becomes a
no-op, so no local `.env` leaks into a test, and the LLM client's three
settings get dummy values, so importing it does not refuse to start.
"""

import os

import dotenv

dotenv.load_dotenv = lambda *args, **kwargs: False

os.environ.setdefault("LLM_BASE_URL", "http://llm.invalid/v1")
os.environ.setdefault("LLM_API_KEY", "dummy")
os.environ.setdefault("LLM_MODEL", "dummy")
