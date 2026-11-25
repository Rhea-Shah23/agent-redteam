import json
from collections import defaultdict
from pathlib import Path

from .attack import CLASSES
from .configs import CONFIGS

RESULTS_DIR = Path(__file__).parent.parent / "results"


def summarize(results: list[dict], model: str) -> dict:
    # one cell per (attack, config): how many trials the check fired in
    cells: dict[tuple, list[int]] = defaultdict(lambda: [0, 0])
    for r in results:
        cell = cells[(r["attack_id"], r["cls"], r["config"])]
        cell[0] += r["success"]
        cell[1] += 1
    return {
        "model": model,
        "cells": [
            {"attack": a, "cls": c, "config": cfg, "successes": k, "trials": n}
            for (a, c, cfg), (k, n) in sorted(cells.items())
        ],
        # raw runs are kept so a finding can point at the exact transcript
        "runs": results,
    }


def _fmt(k: int, n: int) -> str:
    return "-" if n == 0 else f"{k}/{n} ({round(100 * k / n)}%)"


def _configs_in(cells: list[dict]) -> list[str]:
    present = {c["config"] for c in cells}
    return [name for name in CONFIGS if name in present]


def _render_model(summary: dict) -> str:
    cells, configs = summary["cells"], _configs_in(summary["cells"])
    out = [f"## {summary['model']}", ""]

    by_class: dict[tuple, list[int]] = defaultdict(lambda: [0, 0])
    attacks_in_class: dict[str, set] = defaultdict(set)
    for c in cells:
        by_class[(c["cls"], c["config"])][0] += c["successes"]
        by_class[(c["cls"], c["config"])][1] += c["trials"]
        attacks_in_class[c["cls"]].add(c["attack"])

    out += ["### By attack class", "",
            "| class | attacks | " + " | ".join(configs) + " |",
            "|---|---|" + "---|" * len(configs)]
    for cls in CLASSES:
        if cls not in attacks_in_class:
            continue
        row = [_fmt(*by_class[(cls, cfg)]) for cfg in configs]
        out.append(f"| {cls} | {len(attacks_in_class[cls])} | " + " | ".join(row) + " |")
    totals = []
    for cfg in configs:
        k = sum(c["successes"] for c in cells if c["config"] == cfg)
        n = sum(c["trials"] for c in cells if c["config"] == cfg)
        totals.append(f"**{_fmt(k, n)}**")
    n_attacks = len({c["attack"] for c in cells})
    out.append(f"| **all** | **{n_attacks}** | " + " | ".join(totals) + " |")

    by_attack = {(c["attack"], c["config"]): c for c in cells}
    attack_cls = {c["attack"]: c["cls"] for c in cells}
    out += ["", "### By attack", "",
            "| attack | class | " + " | ".join(configs) + " |",
            "|---|---|" + "---|" * len(configs)]
    for attack in sorted(attack_cls, key=lambda a: (CLASSES.index(attack_cls[a]), a)):
        row = []
        for cfg in configs:
            c = by_attack.get((attack, cfg))
            row.append(_fmt(c["successes"], c["trials"]) if c else "-")
        out.append(f"| {attack} | {attack_cls[attack]} | " + " | ".join(row) + " |")
    return "\n".join(out)


def render(summaries: list[dict]) -> str:
    head = (
        "# Scoreboard\n\n"
        "Each cell is the number of trials in which an attack's success check fired, out of the "
        "trials run (k/N, with the percentage). The check is code that inspects the mock world, for "
        "example an order over the limit or an email to an unapproved address. Lower is better for "
        "the defender. Samples are small, so treat single-digit differences as noise.\n"
    )
    return head + "\n" + "\n\n".join(_render_model(s) for s in summaries) + "\n"


def save_model(results: list[dict], model: str, results_dir: Path = RESULTS_DIR) -> Path:
    results_dir.mkdir(exist_ok=True)
    path = results_dir / f"{model}.json"
    path.write_text(json.dumps(summarize(results, model), indent=1) + "\n")
    return path


def write_markdown(results_dir: Path = RESULTS_DIR) -> Path:
    summaries = [json.loads(p.read_text()) for p in sorted(results_dir.glob("*.json"))]
    path = results_dir / "scoreboard.md"
    path.write_text(render(summaries))
    return path
