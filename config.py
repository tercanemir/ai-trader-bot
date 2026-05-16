import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

BASE_URL = "https://ai4trade.ai/api"

EMAIL = os.getenv("AI4TRADE_EMAIL", "").strip()
PASSWORD = os.getenv("AI4TRADE_PASSWORD", "").strip()
AGENT_NAME = os.getenv("AI4TRADE_AGENT_NAME", "emir-bot").strip()
TOKEN = os.getenv("AI4TRADE_TOKEN", "").strip()

HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL_SECONDS", "45"))
COPY_TOP_N = int(os.getenv("COPY_TOP_N", "3"))
MIN_WIN_RATE = float(os.getenv("MIN_WIN_RATE", "0.55"))
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

TOKEN_FILE = Path(__file__).parent / ".token"


def save_token(token: str) -> None:
    TOKEN_FILE.write_text(token.strip())


def load_token() -> str:
    if TOKEN:
        return TOKEN
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text().strip()
    return ""
