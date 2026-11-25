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


TOOLS = {
    "get_price": get_price,
    "place_order": place_order,
    "send_email": send_email,
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
