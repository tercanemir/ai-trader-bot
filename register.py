"""One-time registration script.

Run this once to create the agent account on ai4trade.ai.
On success, saves the JWT token to .token (gitignored).

If the email is already registered, falls back to /login.
"""
import sys

import config
from client import AiTraderClient


def main() -> int:
    if not config.EMAIL or not config.PASSWORD:
        print("ERROR: AI4TRADE_EMAIL and AI4TRADE_PASSWORD must be set in .env")
        return 1

    client = AiTraderClient(token=None)
    print(f"Registering agent: name={config.AGENT_NAME} email={config.EMAIL}")

    try:
        resp = client.register(config.AGENT_NAME, config.EMAIL, config.PASSWORD)
        print("Registration response:", resp)
    except RuntimeError as e:
        msg = str(e)
        if "409" in msg or "exists" in msg.lower() or "duplicate" in msg.lower():
            print("Account already exists, trying login...")
            resp = client.login(config.EMAIL, config.PASSWORD)
            print("Login response:", resp)
        else:
            print("Registration failed:", msg)
            return 1

    token = (
        resp.get("token")
        or resp.get("access_token")
        or resp.get("jwt")
        or (resp.get("data") or {}).get("token")
    )
    if not token:
        print("ERROR: No token in response. Inspect output and adjust register.py.")
        return 1

    config.save_token(token)
    print(f"Token saved to {config.TOKEN_FILE}")

    client.token = token
    try:
        me = client.me()
        print("Agent profile:", me)
    except RuntimeError as e:
        print("Could not fetch profile (token may still be valid):", e)

    return 0


if __name__ == "__main__":
    sys.exit(main())
