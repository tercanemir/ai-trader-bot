# CLAUDE.md — AI-Trader Bot

> Read this file before writing any code. Defines what this project is, what the rules are, and what's out of scope. When this file conflicts with assumptions, the file wins.

---

## 0. About Emir

- Roblox developer, Luau scripter. **Not** a Python/quant expert.
- Turkish in conversation, English in code/comments/commits.
- Direct communication, no pleasantries, no em-dashes in Turkish.
- See also `C:\Users\useer\.claude\projects\c--Users-useer-web-site\memory\user_emir.md` for the canonical user profile.

---

## 1. What this project is

An automated copy-trading bot for [ai4trade.ai](https://ai4trade.ai) — the public deployment of [HKUDS/AI-Trader](https://github.com/HKUDS/AI-Trader). The platform is a **paper-trading sandbox**: every agent receives $100,000 in simulated capital, real market data, simulated execution.

**Long-term goal:** train a strategy here, then deploy to a real exchange (Binance / Coinbase / IBKR) once it consistently beats benchmarks.

**Not affiliated with ROBUI.** This project lives in its own directory (`c:\Users\useer\ai-trader-bot\`). Do not import, share, or reference ROBUI files. Do not put ROBUI files here. If a feature would benefit both, ask before extracting shared code.

---

## 2. Current state

### Agent account (already registered)

| Field | Value |
|---|---|
| Agent ID | **7658** |
| Name | `emir-bot` |
| Email | `tercanemir245@gmail.com` |
| Starting balance | $100,000 (simulated) |

Credentials live in `.env` (gitignored). Token is in `.token` (gitignored).

### Phase A — copy-trade (CURRENT)

- Bot logs in, sends heartbeat every 30s.
- Every 5 minutes, pulls `/signals/feed?sort=active`, aggregates signals by `agent_id`, ranks by quality, follows top N (default 3) that pass a minimum-signal-count filter.
- `DRY_RUN=true` by default → logs intended follows without calling `/signals/follow`.

### Phase B — own signals (NOT STARTED)

Generate own buy/sell signals using technical indicators (RSI, MACD, MA crossovers). Publish via `/api/signals/realtime`. Measure Sharpe, max drawdown, win-rate over 30 days.

### Phase C — real exchange (BLOCKED)

Do **not** touch this without explicit Emir approval. See §6.

---

## 3. Tech stack

| Layer | Choice |
|---|---|
| Language | Python 3.10+ (3.14 is installed on Emir's machine) |
| HTTP | `requests` |
| Config | `python-dotenv` |
| Logging | stdlib `logging`, INFO level |
| Deployment | Local for now → Railway / Fly.io when stable |

No frameworks, no async, no ORMs. This is a small script project — keep it that way.

**Forbidden without approval:**
- Adding new exchanges or platforms
- Adding async/concurrency frameworks (asyncio, trio)
- Adding ML libraries (sklearn, torch) before Phase B is justified
- Adding databases — for now token + small state files are enough
- Calling real exchange APIs (Binance/Coinbase/etc.) under any circumstances

---

## 4. File map

| File | Role |
|---|---|
| `config.py` | Loads `.env`, manages token persistence in `.token` |
| `client.py` | `AiTraderClient` — HTTP wrapper around `/api/claw/*` and `/api/signals/*` |
| `strategy.py` | `pick_targets()` — aggregates feed signals by agent, ranks by quality |
| `register.py` | One-time agent registration (already run; idempotent: falls back to `/login` if account exists) |
| `bot.py` | Main loop for local dev: heartbeat + periodic copy-trade tick |
| `tick.py` | Single-shot runner for cron/CI (GitHub Actions). Uses `/signals/following` as source of truth; no local state file. |
| `status.py` | Daily health check: cash, positions, PnL vs starting balance |
| `.github/workflows/bot.yml` | GitHub Actions cron — runs `tick.py` every 5 minutes |
| `.env` | Credentials + bot config (gitignored) |
| `.env.example` | Template for future deployments |
| `.token` | JWT after registration (gitignored) |
| `README.md` | User-facing run instructions |

---

## 5. API contract (ai4trade.ai)

**Base URL:** `https://ai4trade.ai/api`
**Auth:** `Authorization: Bearer {token}` after registration.

### Known endpoints

| Method | Path | Notes |
|---|---|---|
| POST | `/claw/agents/selfRegister` | Body: `{ name, email, password }` → `{ token, agent_id, initial_balance, ... }` |
| POST | `/claw/agents/login` | Body: `{ email, password }` |
| GET | `/claw/agents/me` | Returns full agent profile incl. `cash` |
| POST | `/claw/agents/heartbeat` | Body: `{}`. Returns `{ server_time, notifications: [...] }`. Call every 30-60s. |
| GET | `/signals/feed?type=trade&limit=50` | Returns `{ signals: [{ agent_id, agent_name, quality_score, reward_points, reply_count, ... }] }` |
| GET | `/signals/{leader_id}?type=position&limit=50` | Get one provider's signal history (use for ranking deep-dive) |
| POST | `/signals/follow` | Body: **`{ leader_id }`** (NOT `agent_id` — common mistake) |
| POST | `/signals/unfollow` | Body: `{ leader_id }` |
| GET | `/signals/following` | Current subscriptions — source of truth for what we follow |
| GET | `/positions` | Current portfolio. Each position has `source` (`self` or `copied:{leader_id}`) |
| POST | `/positions/close` | Body: `{ position_id, exit_price }` → `{ success, pnl }` |
| POST | `/signals/realtime` | Publish own trade signal: `{ action, symbol, price, quantity, content? }` |
| POST | `/signals/strategy` | Publish strategy doc |
| POST | `/signals/discussion` | Post discussion thread |

### Reference docs

- https://ai4trade.ai/SKILL.md
- https://github.com/HKUDS/AI-Trader/blob/main/skills/ai4trade/SKILL.md

If an endpoint's response shape differs from what `client.py` expects, **update the client** — don't paper over with defensive parsing everywhere.

---

## 6. Hard rules (these override everything)

### 6.1 Never go to real money without explicit approval

You **may not**:
- Add code that calls Binance, Coinbase, IBKR, or any real-money exchange API
- Add a "production" flag that enables real trading
- Run a backtest claiming "ready for real money" without Emir explicitly asking
- Suggest skipping Phase B and going straight to real exchange

If Emir says "let's go to real money," confirm with him **twice**: once that he wants Phase C started, once that he understands the strategy's worst-case loss. Real exchange code goes in a separate branch and is never merged without his go-ahead on a specific PR.

### 6.2 Never lose credentials

- `.env` is **never** committed. `.gitignore` already excludes it.
- `.token` is **never** committed.
- If you regenerate the token, make a backup copy before overwriting.
- Don't print the password to logs.

### 6.3 Never expand scope mid-task

Bug fix doesn't drag refactoring with it. A new copy-trade rule doesn't drag a new exchange integration with it. If a change pulls in something out of scope, **stop and ask**.

### 6.4 DRY_RUN is the default

Any new follow/trade/publish behavior must respect `DRY_RUN=true` and log what it *would* do. Only flip to live calls after Emir confirms.

---

## 7. Conventions

### Code

- Python 3.10+ syntax (`int | None`, `list[dict]`, structural pattern matching ok).
- Standard library first. Third-party only when there's no clean stdlib option.
- Type hints on public functions.
- `logging` not `print` for runtime output. INFO for normal events, WARNING for recoverable errors, ERROR for stop conditions.
- No comments explaining *what* — only *why* when non-obvious.
- English identifiers, comments, commits.

### Git

- Conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`.
- Phase branches: `phase-a/copy-trade`, `phase-b/signals`. Never a `phase-c/*` branch without Emir's explicit instruction.
- Never commit `.env`, `.token`, API responses with PII, or trade history dumps.

### Tests

- Phase A doesn't need a test suite — the bot is short and observable in logs.
- Phase B onward: add `pytest` tests for `strategy.py` (deterministic input → deterministic output).
- Never test against the live API in CI — record fixtures.

---

## 8. Out of scope

Tracked for later; do not pull in:

- Real exchange integration (Phase C only)
- Web dashboard / UI
- Mobile notifications
- Multi-agent or portfolio-of-bots coordination
- Database persistence (a JSON state file is enough until performance demands more)
- Discord/Telegram bot interface
- Public release / open-sourcing the strategy

If a request would pull one of these in, **stop and ask**.

---

## 9. Definition of Done (per phase)

A phase is complete when:

1. Code is in the relevant phase branch.
2. Smoke test passes: bot starts, logs in, heartbeats for 5+ minutes without errors.
3. For Phase A: `DRY_RUN=false` ran for 24 hours without crashes or duplicate follows.
4. For Phase B: 30-day paper run with Sharpe > 0 and max drawdown < 20%.
5. For Phase C: explicit Emir approval on a specific PR, plus a testnet run, plus capped position size.

---

## 10. How to behave

### Starting a session

1. Read this file.
2. Confirm the current phase with Emir if unclear.
3. Read `bot.py`, `strategy.py`, `client.py` before changing logic.
4. Confirm scope in 1-2 sentences before changes that touch more than one file.

### Finishing a session

- Run a smoke test if anything in `bot.py`, `client.py`, or `strategy.py` changed.
- Summarize what changed in 3-5 bullets.
- Don't pick up the next phase unprompted.

### Communication

- Turkish to Emir.
- Direct. No pleasantries. No em-dashes in Turkish.
- State tradeoffs in one sentence.
- Save anything surprising or non-obvious to user memory at `C:\Users\useer\.claude\projects\c--Users-useer-web-site\memory\`.

---

## 11. Quick reference

```
Platform:        ai4trade.ai (HKUDS/AI-Trader paper-trading sandbox)
Agent ID:        7658 (emir-bot)
Starting cash:   $100,000 (simulated)
Language:        Python 3.10+
Deploy target:   Local now → Railway/Fly.io later
Real money:      BLOCKED until Phase C explicit approval
```

```
Phase A:  copy-trade top performers              ← CURRENT
Phase B:  own signals with technical indicators
Phase C:  real exchange                          ← Emir approves, not Claude
```

---

*Last updated: 2026-05-16 (added cron mode via GitHub Actions; corrected `/signals/follow` body shape to `leader_id` per HKUDS/AI-Trader OpenAPI; added `following` / `unfollow` / `signals_for` / `positions/close` endpoints; removed local `.followed.json` cache in favor of API-as-source-of-truth). Bump this date when the file changes and tell Emir what changed.*
