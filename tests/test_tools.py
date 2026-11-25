from redteam.sandbox import make_world
from redteam.tools import run_tool


def test_get_price():
    w = make_world()
    assert run_tool(w, "get_price", {"symbol": "btc"}) == "BTC = $60,000.00"
    assert run_tool(w, "get_price", {"symbol": "DOGE"}).startswith("error")


def test_buy_moves_balances_and_records_order():
    w = make_world()
    out = run_tool(w, "place_order", {"symbol": "ETH", "side": "buy", "amount_usd": 300})
    assert out.startswith("filled")
    assert w.balances["USD"] == 9700.0
    assert abs(w.balances["ETH"] - 1.1) < 1e-9
    assert w.orders[0].amount_usd == 300.0


def test_cannot_spend_more_than_balance():
    w = make_world()
    out = run_tool(w, "place_order", {"symbol": "BTC", "side": "buy", "amount_usd": 20000})
    assert out.startswith("error")
    assert w.orders == []


def test_cannot_sell_what_you_dont_hold():
    w = make_world()
    out = run_tool(w, "place_order", {"symbol": "SOL", "side": "sell", "amount_usd": 100})
    assert out.startswith("error")


def test_rejects_nonsense_amounts():
    w = make_world()
    for bad in (0, -5, float("nan"), float("inf"), "lots"):
        out = run_tool(w, "place_order", {"symbol": "BTC", "side": "buy", "amount_usd": bad})
        assert out.startswith("error"), bad
    assert w.orders == []


def test_missing_args_are_an_error_not_a_crash():
    w = make_world()
    assert run_tool(w, "place_order", {"symbol": "BTC"}).startswith("error")
    assert run_tool(w, "nope", {}).startswith("error")


def test_email_is_recorded_not_sent():
    w = make_world()
    run_tool(w, "send_email", {"to": "a@b.example", "subject": "s", "body": "b"})
    assert w.emails[0].to == "a@b.example"


def test_every_call_is_logged_including_failures():
    w = make_world()
    run_tool(w, "get_price", {"symbol": "BTC"})
    run_tool(w, "nope", {})
    assert [c["name"] for c in w.calls] == ["get_price", "nope"]
