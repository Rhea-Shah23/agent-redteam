import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path

import anthropic

from . import scoreboard
from .agent import DEFAULT_MODEL
from .attacks import load_all
from .configs import CONFIGS
from .runner import run_one

RUNS_DIR = Path(__file__).parent.parent / "runs"


def main() -> None:
    p = argparse.ArgumentParser(prog="python -m redteam")
    p.add_argument("--trials", type=int, default=5)
    p.add_argument("--model", action="append", help=f"repeatable, default {DEFAULT_MODEL}")
    p.add_argument("--attack", action="append", help="attack id, repeatable (default: all)")
    p.add_argument("--config", action="append", choices=list(CONFIGS), help="default: all")
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--report-only", action="store_true",
                   help="rebuild results/scoreboard.md from saved results, no API calls")
    args = p.parse_args()

    if args.report_only:
        print(f"wrote {scoreboard.write_markdown()}")
        return

    attacks = [a for a in load_all() if not args.attack or a.id in args.attack]
    configs = [CONFIGS[c] for c in (args.config or CONFIGS)]
    if not attacks:
        p.error("no attacks matched")

    client = anthropic.Anthropic()
    RUNS_DIR.mkdir(exist_ok=True)
    for model in args.model or [DEFAULT_MODEL]:
        print(f"== {model}")
        jobs = [(a, c, t) for a in attacks for c in configs for t in range(args.trials)]
        # If a call fails the rest of the finished runs are already cached,
        # so rerunning the same command picks up where it stopped.
        with ThreadPoolExecutor(args.workers) as pool:
            results = list(pool.map(lambda j: run_one(j[0], j[1], client, model, j[2]), jobs))

        for attack in attacks:
            for config in configs:
                rs = [r for r in results if r.attack_id == attack.id and r.config == config.name]
                fresh = sum(not r.cached for r in rs)
                print(f"{attack.id:28} {config.name:15} {sum(r.success for r in rs)}/{len(rs)}   ({fresh} new calls)")
        tin = sum(r.tokens[0] for r in results)
        tout = sum(r.tokens[1] for r in results)
        print(f"tokens this run: {tin:,} in, {tout:,} out")

        raw = [asdict(r) for r in results]
        stamp = time.strftime("%Y%m%d-%H%M%S")
        (RUNS_DIR / f"{stamp}-{model}.json").write_text(json.dumps(raw, indent=1))
        # a run limited to some attacks would overwrite the full saved results
        if args.attack:
            print("--attack given, not updating results/")
        else:
            print(f"saved {scoreboard.save_model(raw, model)}")

    if not args.attack:
        print(f"wrote {scoreboard.write_markdown()}")


if __name__ == "__main__":
    main()
