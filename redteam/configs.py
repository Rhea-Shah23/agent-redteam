from dataclasses import dataclass

from .agent import BASE_SYSTEM


@dataclass
class Config:
    name: str
    system: str
    # Bump by hand when code behind a config changes but the prompt does not
    # (e.g. the credential layer). Cached runs are keyed on it.
    rev: str = "1"


CONFIGS = {
    "baseline": Config("baseline", BASE_SYSTEM),
}
