from redteam.agent import TradingAgent
from redteam.sandbox import make_world

from .fakes import FakeClient, text_reply, tool_reply


def test_plain_answer_no_tools():
    client = FakeClient([text_reply("hello")])
    agent = TradingAgent(make_world(), client=client)
    assert agent.send("hi") == "hello"
    assert client.requests[0]["system"].startswith("You are TradeBot")


def test_tool_call_runs_and_result_goes_back_to_model():
    client = FakeClient([
        tool_reply("get_price", {"symbol": "BTC"}),
        text_reply("BTC is 60k"),
    ])
    agent = TradingAgent(make_world(), client=client)
    assert agent.send("price?") == "BTC is 60k"

    second = client.requests[1]["messages"]
    result = second[-1]["content"][0]
    assert result["type"] == "tool_result"
    assert result["tool_use_id"] == "toolu_1"
    assert "60,000" in result["content"]
    assert result["is_error"] is False
    assert agent.world.calls[0]["name"] == "get_price"


def test_failed_tool_call_is_flagged_as_error():
    client = FakeClient([tool_reply("fetch_url", {"url": "https://x.example"}), text_reply("ok")])
    agent = TradingAgent(make_world(), client=client)
    agent.send("go")
    assert client.requests[1]["messages"][-1]["content"][0]["is_error"] is True


def test_history_is_kept_across_turns():
    client = FakeClient([text_reply("one"), text_reply("two")])
    agent = TradingAgent(make_world(), client=client)
    agent.send("first")
    agent.send("second")
    roles = [m["role"] for m in client.requests[1]["messages"]]
    assert roles == ["user", "assistant", "user"]


def test_step_limit_stops_a_looping_model():
    client = FakeClient([tool_reply("get_price", {"symbol": "BTC"}) for _ in range(5)])
    agent = TradingAgent(make_world(), client=client, max_steps=3)
    assert "step limit" in agent.send("loop forever")
    assert len(client.requests) == 3


def test_custom_tool_runner_is_used():
    seen = []

    def gate(world, name, args):
        seen.append(name)
        return "error: blocked"

    client = FakeClient([tool_reply("place_order", {"symbol": "BTC", "side": "buy", "amount_usd": 5}),
                         text_reply("blocked")])
    agent = TradingAgent(make_world(), client=client, run_tool=gate)
    agent.send("buy")
    assert seen == ["place_order"]
    assert agent.world.orders == []


def test_thinking_blocks_are_sent_back_unchanged():
    from types import SimpleNamespace as NS
    thinking = NS(type="thinking", thinking="", signature="sig123")
    first = NS(stop_reason="tool_use", content=[
        thinking, NS(type="tool_use", id="t1", name="get_price", input={"symbol": "BTC"})])
    client = FakeClient([first, text_reply("ok")])
    TradingAgent(make_world(), client=client).send("price?")
    sent = client.requests[1]["messages"][1]["content"][0]
    assert sent == {"type": "thinking", "thinking": "", "signature": "sig123"}


def test_tokens_are_summed_across_calls():
    from types import SimpleNamespace as NS
    a = tool_reply("get_price", {"symbol": "BTC"})
    a.usage = NS(input_tokens=100, output_tokens=10)
    b = text_reply("ok")
    b.usage = NS(input_tokens=150, output_tokens=5)
    agent = TradingAgent(make_world(), client=FakeClient([a, b]))
    agent.send("price?")
    assert agent.tokens == [250, 15]
