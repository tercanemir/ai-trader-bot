"""Quick status check: cash, positions, PnL vs starting balance.

Run with: python status.py
"""
import sys

from client import AiTraderClient

STARTING_CASH = 100_000.0


def fmt_money(v: float) -> str:
    sign = "+" if v >= 0 else "-"
    return f"{sign}${abs(v):,.2f}"


def main() -> int:
    c = AiTraderClient()
    if not c.token:
        print("No token. Run `python register.py` first.")
        return 1

    me = c.me()
    pos = c.positions()

    cash = float(pos.get("cash", me.get("cash", 0)))
    positions = pos.get("positions") or []

    position_value = 0.0
    for p in positions:
        qty = float(p.get("quantity") or p.get("qty") or 0)
        price = float(p.get("current_price") or p.get("mark_price") or p.get("price") or 0)
        position_value += qty * price

    equity = cash + position_value
    pnl = equity - STARTING_CASH
    pnl_pct = (pnl / STARTING_CASH) * 100

    print(f"Agent: {me.get('name')} (id {me.get('id')})")
    print(f"Reputation: {me.get('reputation_score')}  Points: {me.get('points')}")
    print()
    print(f"Cash:             ${cash:>12,.2f}")
    print(f"Position value:   ${position_value:>12,.2f}")
    print(f"Equity:           ${equity:>12,.2f}")
    print(f"PnL vs start:     {fmt_money(pnl):>13}  ({pnl_pct:+.2f}%)")
    print()

    if positions:
        print(f"Open positions ({len(positions)}):")
        for p in positions:
            sym = p.get("symbol") or p.get("ticker") or "?"
            qty = p.get("quantity") or p.get("qty") or 0
            entry = p.get("entry_price") or p.get("avg_price") or "?"
            curr = p.get("current_price") or p.get("mark_price") or p.get("price") or "?"
            print(f"  {sym:<10} qty={qty}  entry={entry}  now={curr}")
    else:
        print("No open positions.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
