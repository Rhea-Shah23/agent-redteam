import pkgutil

import redteam.attacks as attacks_pkg
from redteam.attack import CLASSES
from redteam.attacks import load_all


def test_every_attack_is_well_formed():
    attacks = load_all()
    assert len(attacks) >= 3
    ids = [a.id for a in attacks]
    assert len(ids) == len(set(ids)), "duplicate attack ids"
    for a in attacks:
        assert a.cls in CLASSES, a.id
        assert a.turns and all(t.strip() for t in a.turns), a.id
        assert callable(a.check), a.id


def test_attack_id_matches_its_filename():
    files = {m.name for m in pkgutil.iter_modules(attacks_pkg.__path__)}
    assert {a.id for a in load_all()} == files
