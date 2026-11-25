import copy
from types import SimpleNamespace as NS


def text_reply(text: str):
    return NS(stop_reason="end_turn", content=[NS(type="text", text=text)])


def tool_reply(name: str, args: dict, call_id: str = "toolu_1", text: str = ""):
    blocks = [NS(type="tool_use", id=call_id, name=name, input=args)]
    if text:
        blocks.insert(0, NS(type="text", text=text))
    return NS(stop_reason="tool_use", content=blocks)


class FakeClient:
    """Plays back canned responses and remembers what it was asked."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.requests = []
        self.messages = self

    def create(self, **kwargs):
        # deepcopy because the agent keeps appending to the same messages list
        self.requests.append(copy.deepcopy(kwargs))
        return self.replies.pop(0)
