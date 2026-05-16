"""Single-tick runner for cron-driven environments (e.g. GitHub Actions).

Performs one heartbeat + one copy-trade check, then exits. Source of truth
for already-followed leaders is the API itself (/signals/following), so no
local state file or cache is needed.

Run with: python tick.py
"""
import logging
import sys

import config
from client import AiTraderClient
from strategy import pick_targets

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("tick")


def _current_follows(client: AiTraderClient) -> set[int]:
    try:
        resp = client.following()
    except RuntimeError as e:
        log.warning("following() failed (assuming no current follows): %s", e)
        return set()
    items = resp if isinstance(resp, list) else (resp or {}).get("subscriptions") or (resp or {}).get("following") or []
    out: set[int] = set()
    for it in items:
        lid = it.get("leader_id") or it.get("agent_id") or (it.get("leader") or {}).get("id")
        if lid is not None:
            out.add(int(lid))
    return out


def main() -> int:
    client = AiTraderClient()
    if not client.token:
        log.error("No token. Set AI4TRADE_TOKEN env var or run register.py.")
        return 1

    try:
        me = client.me()
        own_id = me.get("id")
        log.info("agent=%s cash=$%.2f reputation=%s",
                 me.get("name"), me.get("cash", 0), me.get("reputation_score"))
    except RuntimeError as e:
        log.error("Token rejected: %s", e)
        return 1

    try:
        hb = client.heartbeat()
        notifs = (hb or {}).get("notifications") or []
        log.info("heartbeat ok notifications=%d", len(notifs))
    except RuntimeError as e:
        log.warning("heartbeat failed: %s", e)

    try:
        feed = client.feed(signal_type="trade", limit=50)
    except RuntimeError as e:
        log.warning("feed fetch failed: %s", e)
        return 0

    signals = (feed or {}).get("signals") or []
    targets = pick_targets(signals, own_agent_id=own_id)
    log.info("feed: %d signals -> %d candidates", len(signals), len(targets))

    followed = _current_follows(client)
    log.info("currently following %d leader(s)", len(followed))

    new_follows = 0
    for bucket in targets:
        aid = int(bucket["agent_id"])
        if aid in followed:
            continue
        avg_q = bucket["quality_sum"] / max(bucket["signal_count"], 1)
        if config.DRY_RUN:
            log.info("[DRY_RUN] would follow %s (%s) avg_quality=%.3f",
                     aid, bucket["agent_name"], avg_q)
            new_follows += 1
            continue
        try:
            client.follow(aid)
            new_follows += 1
            log.info("followed %s (%s) avg_quality=%.3f",
                     aid, bucket["agent_name"], avg_q)
        except RuntimeError as e:
            log.warning("follow failed for %s: %s", aid, e)

    log.info("tick done: %d new follow(s)", new_follows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
