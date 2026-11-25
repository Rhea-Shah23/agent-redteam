import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .agent import DEFAULT_MODEL, TradingAgent
from .attack import Attack, Outcome
from .configs import Config
from .sandbox import Email, Order, World, make_world

CACHE_DIR = Path(__file__).parent.parent / ".cache"


@dataclass
class Result:
    attack_id: str
    cls: str
    config: str
    model: str
    trial: int
    success: bool
    cached: bool
    replies: list[str]
    calls: list[dict]
    orders: list[dict]
    emails: list[dict]
    tokens: list[int]  # [input, output], 0 for cached runs


def _key(attack: Attack, config: Config, model: str, trial: int) -> str:
    # Hash what the model actually sees. The check is deliberately left out: only
    # the (expensive) model run is cached, success is recomputed every time, so
    # I can fix a checker without paying to re-run anything.
    blob = json.dumps({
        "id": attack.id, "turns": attack.turns, "pages": attack.pages, "files": attack.files,
        "config": config.name, "rev": config.rev, "system": config.system,
        "model": model, "trial": trial,
    }, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:24]


def _snapshot(world: World, replies: list[str], tokens: list[int]) -> dict:
    return {
        "replies": replies,
        "calls": world.calls,
        "orders": [asdict(o) for o in world.orders],
        "emails": [asdict(e) for e in world.emails],
        "balances": world.balances,
        "tokens": tokens,
    }


def _outcome(snap: dict, system: str) -> Outcome:
    # Rebuilt world has no files or pages: checks may only look at orders, emails,
    # calls and balances. Keep it that way or the cache stops working.
    world = World(
        files_dir=Path("."), pages={},
        balances=snap["balances"],
        orders=[Order(**o) for o in snap["orders"]],
        emails=[Email(**e) for e in snap["emails"]],
        calls=snap["calls"],
    )
    return Outcome(world=world, replies=snap["replies"], system=system)


def run_one(attack: Attack, config: Config, client, model: str = DEFAULT_MODEL,
            trial: int = 0, cache_dir: Path | None = CACHE_DIR) -> Result:
    path = cache_dir / f"{_key(attack, config, model, trial)}.json" if cache_dir else None
    cached = bool(path and path.exists())

    if cached:
        snap = json.loads(path.read_text())
    else:
        world = make_world(attack.pages, attack.files)
        agent = TradingAgent(world, client=client, model=model, system=config.system)
        replies = [agent.send(turn) for turn in attack.turns]
        snap = _snapshot(world, replies, agent.tokens)
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(snap))

    success = bool(attack.check(_outcome(snap, config.system)))
    return Result(
        attack_id=attack.id, cls=attack.cls, config=config.name, model=model, trial=trial,
        success=success, cached=cached, replies=snap["replies"], calls=snap["calls"],
        orders=snap["orders"], emails=snap["emails"],
        tokens=[0, 0] if cached else snap["tokens"],
    )
