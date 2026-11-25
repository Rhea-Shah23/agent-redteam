import importlib
import pkgutil

from ..attack import Attack


def load_all() -> list[Attack]:
    # each module in this folder defines one ATTACK
    found = []
    for m in pkgutil.iter_modules(__path__):
        found.append(importlib.import_module(f"{__name__}.{m.name}").ATTACK)
    return sorted(found, key=lambda a: a.id)
