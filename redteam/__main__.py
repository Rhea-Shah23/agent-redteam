import argparse
import json
import time
from dataclasses import asdict
from pathlib import Path

import anthropic

from .agent import DEFAULT_MODEL
from .attacks import load_all
from .configs import CONFIGS
from .runner import run_one

RUNS_DIR = Path(__file__).parent.parent / "runs"


def main() -> None:
    p = argparse.ArgumentParser(prog="python -m redteam")
    p.add_argument("--trials", type=int, default=3)
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--attack", action="append", help="attack id, repeatable (default: all)")
    p.add_argument("--config", action="append", choices=list(CONFIGS), help="default: all")
    args = p.parse_args()

    attacks = [a for a in load_all() if not args.attack or a.id in args.attack]
    configs = [CONFIGS[c] for c in (args.config or CONFIGS)]
    if not attacks:
        p.error("no attacks matched")

    client = anthropic.Anthropic()
    results = []
    spent = [0, 0]
    for attack in attacks:
        for config in configs:
            rs = [run_one(attack, config, client, args.model, t) for t in range(args.trials)]
            results.extend(rs)
            for r in rs:
                spent[0] += r.tokens[0]
                spent[1] += r.tokens[1]
            wins = sum(r.success for r in rs)
            fresh = sum(not r.cached for r in rs)
            print(f"{attack.id:28} {config.name:10} {wins}/{len(rs)}   ({fresh} new calls)")

    RUNS_DIR.mkdir(exist_ok=True)
    out = RUNS_DIR / f"{time.strftime('%Y%m%d-%H%M%S')}.json"
    out.write_text(json.dumps([asdict(r) for r in results], indent=1))
    print(f"tokens this run: {spent[0]:,} in, {spent[1]:,} out")
    print(f"saved {out}")


if __name__ == "__main__":
    main()
