"""Market data and paper-trading helpers. No exchange orders are placed."""
import requests

COINS = {
    "BTC": ("bitcoin", "Bitcoin"),
    "ETH": ("ethereum", "Ethereum"),
    "SOL": ("solana", "Solana"),
    "ADA": ("cardano", "Cardano"),
    "XRP": ("ripple", "XRP"),
}


def fetch_prices():
    ids = ",".join(coin_id for coin_id, _ in COINS.values())
    response = requests.get(
        "https://api.coingecko.com/api/v3/simple/price",
        params={"ids": ids, "vs_currencies": "eur", "include_24hr_change": "true"},
        headers={"accept": "application/json", "User-Agent": "crypto-ai-v3-paper-trading/1.0"},
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()
    result = {}
    for symbol, (coin_id, name) in COINS.items():
        item = payload.get(coin_id, {})
        price = item.get("eur")
        if not isinstance(price, (int, float)) or price <= 0:
            raise ValueError(f"Prix indisponible pour {symbol}")
        result[symbol] = {"name": name, "price": float(price), "change_24h": item.get("eur_24h_change")}
    return result


def portfolio_value(cash, positions, prices):
    return cash + sum(qty * prices[symbol]["price"] for symbol, qty in positions.items())
