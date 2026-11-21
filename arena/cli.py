import argparse
import json
import logging
import time
from .agent import Agent
from .config import load_config
from .delphi_client import DelphiClient, MockDelphiClient
from .markets import load_markets
from .models import parse_time, utcnow
from .rules import TIMELINE
from .state import State


def main(argv=None):
    parser = argparse.ArgumentParser(prog="arena")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("run-once", "loop", "markets", "status", "receipts", "feedback", "check-config"):
        cmd = sub.add_parser(name)
        mode = cmd.add_mutually_exclusive_group()
        mode.add_argument("--dry-run", action="store_true")
        mode.add_argument("--live", action="store_true")
        cmd.add_argument("--markets")
        cmd.add_argument("--provider", choices=("local", "ddg", "rss", "direct"))
        cmd.add_argument("--out", default="out")
        if name == "feedback":
            cmd.add_argument("text")
        if name == "loop":
            cmd.add_argument("--interval", type=float, default=60)
            cmd.add_argument("--until", default=TIMELINE["deadline"])
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    config = load_config()
    if args.live or args.dry_run:
        config.dry_run = not args.live
    if args.provider:
        config.provider = args.provider
    try:
        config.validate()
        state = State(config.state_path)
        client = MockDelphiClient(state) if config.dry_run else DelphiClient(config)
        agent = Agent(config, state, client, args.out, args.markets)
        if args.command == "check-config":
            print(f"Configuration OK: {'SAMPLE dry-run' if config.dry_run else 'LIVE; operator-verified schema'}")
        elif args.command == "run-once":
            agent.cycle()
        elif args.command == "loop":
            if args.interval <= 0:
                raise ValueError("interval must be positive")
            until = parse_time(args.until)
            try:
                while utcnow() < until:
                    agent.cycle()
                    time.sleep(min(args.interval * 60, max(0, (until - utcnow()).total_seconds())))
            except KeyboardInterrupt:
                print("Stopped gracefully; persisted pending keys retained.")
        elif args.command == "markets":
            for market in load_markets(args.markets, client):
                print(json.dumps(market.__dict__))
        elif args.command == "status":
            ids = sorted({r["market_id"] for r in state.rows()})
            for market_id in ids:
                print(f"{market_id}: {state.count_for_market(market_id)}/3 slots reserved")
            progress = state.eligibility()
            print(f'Eligibility: {progress["judged"]}/10 judged across {progress["markets"]}/3 markets (mock receipts excluded)')
        elif args.command == "receipts":
            agent.poll_receipts()
            for row in state.rows():
                print(row["receipt"] or "pending")
        elif args.command == "feedback":
            print(json.dumps(client.send_feedback(args.text)))
    except (ValueError, OSError) as exc:
        parser.exit(2, f"Error: {exc}\n")
