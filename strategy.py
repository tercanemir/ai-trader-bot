"""Copy-trade strategy: pick top N agents from the signal feed.

The /signals/feed endpoint returns individual signals, not agent stats.
We aggregate by agent_id and rank by platform-provided quality_score.
"""
from collections import defaultdict
from typing import Iterable

import config


def _aggregate_by_agent(signals: Iterable[dict]) -> dict[int, dict]:
    buckets: dict[int, dict] = defaultdict(lambda: {
        "agent_id": None,
        "agent_name": "",
        "signal_count": 0,
        "quality_sum": 0.0,
        "reward_sum": 0,
        "reply_sum": 0,
    })
    for sig in signals:
        aid = sig.get("agent_id")
        if aid is None:
            continue
        b = buckets[aid]
        b["agent_id"] = aid
        b["agent_name"] = sig.get("agent_name") or b["agent_name"]
        b["signal_count"] += 1
        b["quality_sum"] += float(sig.get("quality_score") or 0)
        b["reward_sum"] += int(sig.get("reward_points") or 0)
        b["reply_sum"] += int(sig.get("reply_count") or 0)
    return buckets


def _score(bucket: dict) -> float:
    n = bucket["signal_count"]
    if n < 2:
        return -1
    avg_quality = bucket["quality_sum"] / n
    # weight: average quality dominates, with small bonuses for activity and engagement
    return avg_quality * 10 + (bucket["reward_sum"] * 0.05) + (bucket["reply_sum"] * 0.2)


def pick_targets(signals: Iterable[dict], own_agent_id: int | None = None) -> list[dict]:
    buckets = _aggregate_by_agent(signals)
    if own_agent_id is not None:
        buckets.pop(own_agent_id, None)

    ranked = sorted(buckets.values(), key=_score, reverse=True)
    return [b for b in ranked[: config.COPY_TOP_N] if _score(b) > 0]
