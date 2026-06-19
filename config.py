import os

from dotenv import load_dotenv

load_dotenv()

KAGI_API_KEY = os.environ["KAGI_API_KEY"] or "MISSING"
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"] or "MISSING"

if KAGI_API_KEY == "MISSING" or OPENROUTER_API_KEY == "MISSING":
    raise ValueError("api key missing")
