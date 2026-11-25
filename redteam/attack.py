from dataclasses import dataclass, field
from typing import Callable

from .sandbox import World

CLASSES = (
    "direct_injection",
    "indirect_injection",
    "tool_args",
    "spend_limit",
    "prompt_extraction",
    "multi_turn",
)


@dataclass
class Outcome:
    # what a success check gets to look at after the attack has played out
    world: World
    replies: list[str]
    system: str


@dataclass
class Attack:
    id: str
    cls: str
    turns: list[str]
    check: Callable[[Outcome], bool]
    pages: dict[str, str] = field(default_factory=dict)
    files: dict[str, str] = field(default_factory=dict)
    why: str = ""
