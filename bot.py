"""Main loop: heartbeat + copy-trade.

Run with: python bot.py
"""
import logging
import signal
import sys
import time

import config
from client import AiTraderClient
from strategy import pick_targets

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("bot")

_running = True


def _shutdown(signum, frame):
    global _running
    log.info("Shutdown signal received")
    _running = False


def heartbeat_tick(client: AiTraderClient) -> None:
    try:
        resp = client.heartbeat()
        notifications = (resp or {}).get("notifications") or []
        if notifications:
            log.info("Heartbeat: %d notification(s)", len(notifications))
        else:
            log.debug("Heartbeat ok")
    except RuntimeError as e:
        log.warning("Heartbeat failed: %s", e)


def copy_trade_tick(client: AiTraderClient, followed: set[int], own_id: int | None) -> None:
    try:
        feed = client.feed(signal_type="trade", limit=50)
    except RuntimeError as e:
        log.warning("Feed fetch failed: %s", e)
        return

    signals = (feed or {}).get("signals") or []
    targets = pick_targets(signals, own_agent_id=own_id)
    if not targets:
        log.info("No candidates pass filters")
        return

    for bucket in targets:
        aid = int(bucket["agent_id"])
        if aid in followed:
            continue
        avg_q = bucket["quality_sum"] / max(bucket["signal_count"], 1)
        if config.DRY_RUN:
            log.info("[DRY_RUN] would follow agent %s (%s) signals=%d avg_quality=%.3f",
                     aid, bucket["agent_name"], bucket["signal_count"], avg_q)
            followed.add(aid)
            continue
        try:
            client.follow(aid)
            followed.add(aid)
            log.info("Followed agent %s (%s) avg_quality=%.3f", aid, bucket["agent_name"], avg_q)
        except RuntimeError as e:
            log.warning("Follow failed for %s: %s", aid, e)


def main() -> int:
    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    client = AiTraderClient()
    if not client.token:
        log.error("No token. Run `python register.py` first.")
        return 1

    log.info("Bot starting. DRY_RUN=%s heartbeat=%ds top_n=%d",
             config.DRY_RUN, config.HEARTBEAT_INTERVAL, config.COPY_TOP_N)

    try:
        me = client.me()
        own_id = me.get("id")
        log.info("Logged in as agent %s (%s) cash=%s", own_id, me.get("name"), me.get("cash"))
    except RuntimeError as e:
        log.error("Token rejected: %s. Re-run register.py.", e)
        return 1

    followed: set[int] = set()
    last_copy_check = 0.0
    copy_check_interval = 300

    while _running:
        heartbeat_tick(client)

        now = time.time()
        if now - last_copy_check > copy_check_interval:
            copy_trade_tick(client, followed, own_id)
            last_copy_check = now

        for _ in range(config.HEARTBEAT_INTERVAL):
            if not _running:
                break
            time.sleep(1)

    log.info("Bot stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
