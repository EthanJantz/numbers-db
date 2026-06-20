import os

# config.py reads these at import time (and main.py imports config). Provide
# dummy values so tests can import main without real credentials. setdefault
# leaves any real local .env values untouched.
os.environ.setdefault("KAGI_API_KEY", "test-key")
os.environ.setdefault("OPENROUTER_API_KEY", "test-key")
