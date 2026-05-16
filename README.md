# AI-Trader Bot

Automated copy-trading bot for [ai4trade.ai](https://ai4trade.ai) — a paper-trading sandbox by HKUDS/AI-Trader.

**Not affiliated with ROBUI. This is a separate project.**

## Phase A — Copy-trade top performers

The bot registers an agent, sends heartbeats, and follows the top-N traders on the platform feed that pass a win-rate filter. No own signals yet.

## Setup

1. Install Python 3.10+ and `pip install -r requirements.txt`.
2. `.env` is already populated. **Back up the password somewhere safe** — losing it means losing the account.
3. Register the agent (one time):
   ```
   python register.py
   ```
   On success, a JWT token is saved to `.token` (gitignored).
4. Start the bot:
   ```
   python bot.py
   ```

Bot defaults to `DRY_RUN=true` — it logs what it *would* follow without actually calling `/signals/follow`. Flip to `false` in `.env` when you're satisfied with the picks.

## Config (`.env`)

| Key | Default | Meaning |
|---|---|---|
| `HEARTBEAT_INTERVAL_SECONDS` | 45 | How often to ping `/heartbeat` |
| `COPY_TOP_N` | 3 | How many top agents to follow |
| `MIN_WIN_RATE` | 0.55 | Skip agents below this win-rate |
| `DRY_RUN` | true | When true, no real follow calls |

## Files

- `config.py` — env loading, token storage
- `client.py` — HTTP wrapper around `/api/claw/*` and `/api/signals/*`
- `strategy.py` — scoring/filtering top traders
- `register.py` — one-time registration
- `bot.py` — main loop

## Roadmap

- **A** (current): copy-trade top performers, paper only
- **B**: own signal generation with technical indicators
- **C**: real exchange — only after B proves profitable

## Notes

- ai4trade is paper-trading; profits/losses are simulated.
- Endpoint shapes are inferred from public SKILL.md; adjust `client.py` if responses differ.
