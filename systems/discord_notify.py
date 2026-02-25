# -*- coding: utf-8 -*-
"""Claws of Doom — Discord notification module.

Sends rich embeds for system status, new picks, and trade exits.
Runs as a post-scan step in the GitHub Actions workflow.
"""

import json
import os
import sys
import requests

DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL", "")
DASHBOARD_URL = "https://eltonaguiar.github.io/CLAWSOFDOOM/"
VERSION = "3.1.0"

COLORS = {
    "status_green": 0x00FF66,
    "status_red": 0xFF3333,
    "status_neutral": 0xFF6600,
    "new_pick": 0x00FF66,
    "exit_win": 0xFFCC00,
    "exit_loss": 0xFF3333,
}


def post(payload):
    if not DISCORD_WEBHOOK:
        print("  [Discord] No webhook configured, skipping")
        return
    try:
        r = requests.post(DISCORD_WEBHOOK, json=payload, timeout=10)
        print(f"  [Discord] Sent ({r.status_code})")
    except Exception as e:
        print(f"  [Discord] Failed: {e}")


def fg_label(value):
    if value <= 20:
        return f"{value} (EXTREME FEAR)"
    if value <= 40:
        return f"{value} (Fear)"
    if value <= 60:
        return f"{value} (Neutral)"
    if value <= 80:
        return f"{value} (Greed)"
    return f"{value} (EXTREME GREED)"


def pnl_sign(v):
    return "+" if v >= 0 else ""


def send_status(picks_data, active_picks, closed_picks):
    """Send system status embed with performance history."""
    perf = picks_data.get("performance", {})
    ms = picks_data.get("market_snapshot", {})
    fg = ms.get("fear_greed", 0)

    total_closed = len(closed_picks)
    wins = sum(1 for c in closed_picks if c.get("exit_reason") == "TP_HIT")
    losses = total_closed - wins
    wr = (wins / total_closed * 100) if total_closed > 0 else 0
    total_pnl = sum(c.get("realized_pnl_pct", 0) for c in closed_picks)
    total_pnl_dollar = sum(c.get("realized_pnl_dollar", 0) for c in closed_picks)

    # Color based on win rate
    if wr >= 60:
        color = COLORS["status_green"]
    elif wr >= 40:
        color = COLORS["status_neutral"]
    else:
        color = COLORS["status_red"]

    fields = [
        {"name": "Active Picks", "value": str(len(active_picks)), "inline": True},
        {"name": "Closed", "value": f"{wins}W / {losses}L ({total_closed} total)", "inline": True},
        {"name": "Win Rate", "value": f"**{wr:.1f}%**", "inline": True},
        {"name": "Realized PnL", "value": f"**{pnl_sign(total_pnl)}{total_pnl:.2f}%** ({pnl_sign(total_pnl_dollar)}${abs(total_pnl_dollar):.2f})", "inline": True},
        {"name": "F&G Index", "value": fg_label(fg), "inline": True},
        {"name": "Strategies", "value": "6 active (3L/2S/1C)", "inline": True},
    ]

    # Active picks with unrealized P&L
    if active_picks:
        lines = []
        for p in active_picks[:8]:
            pnl_pct = p.get("unrealized_pnl_pct", 0)
            direction = p.get("direction", "LONG")
            lines.append(
                f"`{p['symbol']:10s}` {direction} {pnl_sign(pnl_pct)}{pnl_pct:.2f}%"
            )
        unrealized_total = sum(p.get("unrealized_pnl_pct", 0) for p in active_picks)
        lines.append(f"**Unrealized: {pnl_sign(unrealized_total)}{unrealized_total:.2f}%**")
        fields.append({"name": "Open Positions", "value": "\n".join(lines)})

    embed = {
        "title": f"CLAWS OF DOOM v{VERSION} — System F Status",
        "color": color,
        "fields": fields,
        "footer": {"text": f"System F — Claws of Doom | {DASHBOARD_URL}"},
        "url": DASHBOARD_URL,
    }
    post({"embeds": [embed]})


def send_new_picks(new_picks, fg):
    """Send alerts for new picks generated this scan."""
    for p in new_picks:
        direction = p.get("direction", "LONG")
        dir_color = COLORS["new_pick"] if direction == "LONG" else COLORS["exit_loss"]

        embed = {
            "title": f"CLAWS OF DOOM — New {direction}: {p['symbol']}",
            "color": dir_color,
            "fields": [
                {"name": "Strategy", "value": p.get("strategy_name", p.get("strategy", "unknown")), "inline": True},
                {"name": "Entry", "value": f"${p['entry_price']:,.2f}", "inline": True},
                {"name": "Target", "value": f"${p['tp_price']:,.2f} (+{((p['tp_price']/p['entry_price']-1)*100):.1f}%)", "inline": True},
                {"name": "Stop Loss", "value": f"${p['sl_price']:,.2f} (-{((1-p['sl_price']/p['entry_price'])*100):.1f}%)", "inline": True},
                {"name": "Confidence", "value": f"{(p.get('confidence', 0)*100):.0f}%", "inline": True},
                {"name": "F&G", "value": fg_label(fg), "inline": True},
            ],
            "description": p.get("reason", ""),
            "footer": {"text": f"System F — Claws of Doom v{VERSION}"},
            "url": DASHBOARD_URL,
        }
        post({"embeds": [embed]})


def send_closed_picks(newly_closed):
    """Send alerts for picks that just closed (TP or SL hit)."""
    for c in newly_closed:
        pnl = c.get("realized_pnl_pct", 0)
        is_win = c.get("exit_reason") == "TP_HIT"
        color = COLORS["exit_win"] if is_win else COLORS["exit_loss"]
        label = "WIN" if is_win else "LOSS"

        embed = {
            "title": f"CLAWS OF DOOM — {label}: {c['symbol']} ({pnl_sign(pnl)}{pnl:.2f}%)",
            "color": color,
            "fields": [
                {"name": "Entry", "value": f"${c.get('entry_price', 0):,.2f}", "inline": True},
                {"name": "Exit", "value": f"${c.get('exit_price', 0):,.2f}", "inline": True},
                {"name": "PnL", "value": f"**{pnl_sign(pnl)}{pnl:.2f}%** ({pnl_sign(c.get('realized_pnl_dollar', 0))}${abs(c.get('realized_pnl_dollar', 0)):.2f})", "inline": True},
                {"name": "Strategy", "value": c.get("strategy", "unknown"), "inline": True},
                {"name": "Exit Reason", "value": c.get("exit_reason", "unknown"), "inline": True},
            ],
            "footer": {"text": f"System F — Claws of Doom v{VERSION}"},
        }
        post({"embeds": [embed]})


def main():
    """Load pick data and send Discord notifications."""
    print("=== Claws of Doom — Discord Notifications ===")

    docs_dir = os.path.join(os.path.dirname(__file__), "..", "docs")

    # Load current picks data
    picks_path = os.path.join(docs_dir, "picks.json")
    active_path = os.path.join(docs_dir, "active_picks.json")
    closed_path = os.path.join(docs_dir, "closed_picks.json")

    try:
        with open(picks_path) as f:
            picks_data = json.load(f)
    except Exception:
        picks_data = {}

    try:
        with open(active_path) as f:
            active_picks = json.load(f)
    except Exception:
        active_picks = []

    try:
        with open(closed_path) as f:
            closed_picks = json.load(f)
    except Exception:
        closed_picks = []

    if not DISCORD_WEBHOOK:
        print("  DISCORD_WEBHOOK_URL not set, exiting")
        return

    # Detect newly opened/closed picks by comparing with previous state
    # The engine already tracks this in picks.json
    new_picks = picks_data.get("picks", [])
    recently_closed = picks_data.get("closed_picks_recent", [])

    # Always send system status
    send_status(picks_data, active_picks, closed_picks)

    # Send alerts for new picks
    if new_picks:
        fg = picks_data.get("market_snapshot", {}).get("fear_greed", 0)
        send_new_picks(new_picks, fg)

    # Send alerts for recently closed picks
    if recently_closed:
        send_closed_picks(recently_closed)

    print(f"  Status: {len(active_picks)} active, {len(closed_picks)} closed, {len(new_picks)} new scan picks")
    print("  Done.")


if __name__ == "__main__":
    main()
