import os

from dotenv import load_dotenv

load_dotenv()

KAGI_API_KEY = os.environ["KAGI_API_KEY"] or "MISSING"

if KAGI_API_KEY == "MISSING":
    raise ValueError("KAGI_API_KEY missing")
