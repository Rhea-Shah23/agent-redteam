import math

from .sandbox import PRICES, Email, Order, World


def get_price(world: World, symbol: str) -> str:
    price = PRICES.get(str(symbol).upper())
    if price is None:
        return f"error: unknown symbol {symbol}"
    return f"{str(symbol).upper()} = ${price:,.2f}"


def place_order(world: World, symbol: str, side: str, amount_usd: float) -> str:
    symbol = str(symbol).upper()
    if symbol not in PRICES:
        return f"error: unknown symbol {symbol}"
    if side not in ("buy", "sell"):
        return "error: side must be buy or sell"
    amount = float(amount_usd)
    if not math.isfinite(amount) or amount <= 0:
        return "error: amount_usd must be a positive number"

    qty = amount / PRICES[symbol]
    # No spending limit here on purpose. The tool is the baseline "dumb" backend,
    # limits live in the prompt or in the credential layer, which is what we test.
    if side == "buy":
        if world.balances["USD"] < amount:
            return "error: insufficient USD balance"
        world.balances["USD"] -= amount
        world.balances[symbol] = world.balances.get(symbol, 0.0) + qty
    else:
        if world.balances.get(symbol, 0.0) < qty:
            return f"error: insufficient {symbol} balance"
        world.balances[symbol] -= qty
        world.balances["USD"] += amount

    world.orders.append(Order(symbol, side, amount, qty))
    return f"filled: {side} {qty:.6f} {symbol} for ${amount:,.2f}"


def send_email(world: World, to: str, subject: str, body: str) -> str:
    world.emails.append(Email(str(to), str(subject), str(body)))
    return f"sent email to {to}"


def fetch_url(world: World, url: str) -> str:
    # exact match against the fixture pages, nothing here touches the network
    page = world.pages.get(str(url))
    if page is None:
        return "error: 404 not found"
    return page


MAX_FILE_CHARS = 20000


def read_file(world: World, path: str) -> str:
    root = world.files_dir.resolve()
    # resolve() follows symlinks and collapses "..", so checking the result
    # covers traversal and symlink escapes in one go
    target = (root / str(path)).resolve()
    if not target.is_relative_to(root):
        return "error: path is outside the allowed directory"
    if not target.is_file():
        return "error: file not found"
    return target.read_text(errors="replace")[:MAX_FILE_CHARS]


TOOLS = {
    "get_price": get_price,
    "place_order": place_order,
    "send_email": send_email,
    "fetch_url": fetch_url,
    "read_file": read_file,
}


def run_tool(world: World, name: str, args: dict) -> str:
    fn = TOOLS.get(name)
    if fn is None:
        result = f"error: no such tool {name}"
    else:
        try:
            result = fn(world, **args)
        except (TypeError, ValueError) as e:
            # model sent missing or badly typed args
            result = f"error: bad arguments ({e})"
    world.calls.append({"name": name, "args": args, "result": result})
    return result


def _schema(name: str, description: str, **props: dict) -> dict:
    return {
        "name": name,
        "description": description,
        "input_schema": {
            "type": "object",
            "properties": props,
            "required": list(props),
        },
    }


SCHEMAS = [
    _schema("get_price", "Get the current USD price of a coin.",
            symbol={"type": "string", "description": "BTC, ETH or SOL"}),
    _schema("place_order", "Place a market order for a coin, sized in USD.",
            symbol={"type": "string"},
            side={"type": "string", "enum": ["buy", "sell"]},
            amount_usd={"type": "number"}),
    _schema("send_email", "Send an email.",
            to={"type": "string"}, subject={"type": "string"}, body={"type": "string"}),
    _schema("fetch_url", "Fetch the text of a web page.",
            url={"type": "string"}),
    _schema("read_file", "Read a text file from the user's documents folder.",
            path={"type": "string", "description": "relative path, e.g. notes.txt"}),
]
