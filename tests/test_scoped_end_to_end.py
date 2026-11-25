"""Scripted models run through the real runner against the scoped config.
Same "model falls for it" scripts as the baseline replays, but now the tool
layer is in the way and the check must stay quiet."""
import pytest

from redteam.attacks import load_all
from redteam.configs import CONFIGS
from redteam.runner import run_one

from .fakes import FakeClient
from .test_attack_replays import DONE, SCRIPTS

# These scripts include steps the gate does not stop on its own: a read of notes.txt,
# a fetch, or a request the model simply refuses. They are fine to include,
# the point is that no check ever fires.
ATTACKS = load_all()


@pytest.mark.parametrize("attack", ATTACKS, ids=lambda a: a.id)
def test_scripted_fall_is_stopped_by_the_gate(attack, tmp_path):
    falls, _ = SCRIPTS[attack.id]
    if attack.id.startswith("extract_"):
        pytest.skip("prompt extraction is a reply, not a tool call, the gate cannot see it")
    client = FakeClient(list(falls) + [DONE] * 20)
    r = run_one(attack, CONFIGS["scoped_creds"], client, cache_dir=tmp_path)
    assert not r.success, [c["result"] for c in r.calls]


def test_denial_text_reaches_the_model(tmp_path):
    attack = next(a for a in ATTACKS if a.id == "coin_units_over_limit")
    falls, _ = SCRIPTS[attack.id]
    client = FakeClient(list(falls) + [DONE])
    run_one(attack, CONFIGS["scoped_creds"], client, cache_dir=tmp_path)
    sent = client.requests[1]["messages"][-1]["content"][0]
    assert sent["is_error"] and "per-order cap" in sent["content"]
