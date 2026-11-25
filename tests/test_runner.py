from redteam import checks
from redteam.attack import Attack
from redteam.configs import Config
from redteam.runner import run_one

from .fakes import FakeClient, text_reply, tool_reply

CONFIG = Config("test", "You are a test bot.")


def over_limit_attack(**kw):
    return Attack(id="t", cls="spend_limit", turns=["buy big"], check=checks.order_over_limit, **kw)


def buy(amount):
    return tool_reply("place_order", {"symbol": "BTC", "side": "buy", "amount_usd": amount})


def test_success_when_the_check_fires(tmp_path):
    client = FakeClient([buy(5000), text_reply("done")])
    r = run_one(over_limit_attack(), CONFIG, client, cache_dir=tmp_path)
    assert r.success and r.orders[0]["amount_usd"] == 5000
    assert r.replies == ["done"]


def test_no_success_when_the_model_refuses(tmp_path):
    client = FakeClient([text_reply("no")])
    assert not run_one(over_limit_attack(), CONFIG, client, cache_dir=tmp_path).success


def test_no_success_for_a_small_order(tmp_path):
    client = FakeClient([buy(100), text_reply("done")])
    assert not run_one(over_limit_attack(), CONFIG, client, cache_dir=tmp_path).success


def test_all_turns_are_sent_in_order(tmp_path):
    a = Attack(id="mt", cls="multi_turn", turns=["one", "two"], check=lambda o: False)
    client = FakeClient([text_reply("a"), text_reply("b")])
    r = run_one(a, CONFIG, client, cache_dir=tmp_path)
    assert r.replies == ["a", "b"]
    assert client.requests[1]["messages"][-1]["content"] == "two"


def test_second_run_comes_from_cache_without_calling_the_model(tmp_path):
    first = FakeClient([buy(5000), text_reply("done")])
    run_one(over_limit_attack(), CONFIG, first, cache_dir=tmp_path)

    second = FakeClient([])
    r = run_one(over_limit_attack(), CONFIG, second, cache_dir=tmp_path)
    assert r.cached and r.success
    assert second.requests == []


def test_changing_the_check_does_not_need_a_new_model_run(tmp_path):
    run_one(over_limit_attack(), CONFIG, FakeClient([buy(5000), text_reply("x")]), cache_dir=tmp_path)
    stricter = Attack(id="t", cls="spend_limit", turns=["buy big"], check=lambda o: False)
    r = run_one(stricter, CONFIG, FakeClient([]), cache_dir=tmp_path)
    assert r.cached and not r.success


def test_cache_is_keyed_on_trial_prompt_and_attack_content(tmp_path):
    def go(attack=None, config=CONFIG, trial=0):
        client = FakeClient([text_reply("x")])
        run_one(attack or over_limit_attack(), config, client, trial=trial, cache_dir=tmp_path)
        return len(client.requests)  # 1 means it missed the cache

    assert go() == 1
    assert go() == 0
    assert go(trial=1) == 1
    assert go(config=Config("test", "different prompt")) == 1
    assert go(attack=over_limit_attack(pages={"u": "p"})) == 1
    assert go(config=Config("test", CONFIG.system, rev="2")) == 1
