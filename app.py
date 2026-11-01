import os, json, time
from pathlib import Path
from datetime import datetime, date
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False
DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
DATA_DIR.mkdir(exist_ok=True)
PORTFOLIO_FILE = DATA_DIR / "portfolio.json"
API_KEY = os.getenv("TWELVE_DATA_API_KEY", "").strip()
API_BASE = "https://api.twelvedata.com"

SEED = {
    "holdings": [],
    "manual_dividends": [],
    "watchlist": [
        {"symbol":"AAPL","exchange":"NASDAQ","market":"US","name":"Apple Inc."},
        {"symbol":"MSFT","exchange":"NASDAQ","market":"US","name":"Microsoft"},
        {"symbol":"RELIANCE","exchange":"NSE","market":"IN","name":"Reliance Industries"},
        {"symbol":"TCS","exchange":"NSE","market":"IN","name":"Tata Consultancy Services"}
    ]
}

def load_data():
    if not PORTFOLIO_FILE.exists():
        save_data(SEED)
    try:
        return json.loads(PORTFOLIO_FILE.read_text(encoding="utf-8"))
    except Exception:
        return json.loads(json.dumps(SEED))

def save_data(data):
    tmp = PORTFOLIO_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(PORTFOLIO_FILE)

def api_get(endpoint, params):
    if not API_KEY:
        raise RuntimeError("Add your Twelve Data API key as TWELVE_DATA_API_KEY to enable live market data.")
    params = dict(params)
    params["apikey"] = API_KEY
    try:
        r = requests.get(f"{API_BASE}/{endpoint}", params=params, timeout=15)
        r.raise_for_status()
        payload = r.json()
    except requests.RequestException as exc:
        raise RuntimeError(f"Market data request failed: {exc}")
    if isinstance(payload, dict) and payload.get("status") == "error":
        raise RuntimeError(payload.get("message", "Market data provider returned an error."))
    if isinstance(payload, dict) and payload.get("code"):
        raise RuntimeError(payload.get("message", "Market data provider returned an error."))
    return payload

def normalize_symbol(symbol, market, exchange):
    symbol = (symbol or "").strip().upper()
    if not symbol:
        raise ValueError("Enter a ticker symbol.")
    market = (market or "US").upper()
    if market == "IN":
        exch = (exchange or "NSE").upper()
        return f"{symbol}:{exch}"
    return symbol

@app.get("/")
def index():
    return render_template("index.html")

@app.get("/api/portfolio")
def portfolio():
    data = load_data()
    return jsonify(data)

@app.post("/api/holding")
def add_holding():
    body = request.get_json(force=True)
    try:
        symbol = normalize_symbol(body.get("symbol"), body.get("market"), body.get("exchange"))
        quantity = float(body.get("quantity", 0))
        avg_price = float(body.get("avg_price", 0))
        if quantity <= 0 or avg_price <= 0:
            raise ValueError("Quantity and average buy price must be greater than zero.")
        if quantity > 1e12 or avg_price > 1e12:
            raise ValueError("Value is too large.")
        data = load_data()
        holding = {
            "id": str(int(time.time() * 1000)),
            "symbol": symbol,
            "display_symbol": body.get("symbol", "").upper().strip(),
            "market": body.get("market", "US").upper(),
            "exchange": body.get("exchange", "NASDAQ" if body.get("market","US").upper()=="US" else "NSE").upper(),
            "name": (body.get("name") or symbol).strip()[:80],
            "quantity": quantity,
            "avg_price": avg_price,
            "currency": "INR" if body.get("market","US").upper()=="IN" else "USD"
        }
        data["holdings"].append(holding)
        save_data(data)
        return jsonify({"ok": True, "holding": holding})
    except (ValueError, TypeError) as exc:
        return jsonify({"error": str(exc)}), 400

@app.delete("/api/holding/<holding_id>")
def delete_holding(holding_id):
    data = load_data()
    before = len(data["holdings"])
    data["holdings"] = [h for h in data["holdings"] if h["id"] != holding_id]
    save_data(data)
    return jsonify({"ok": True, "deleted": before - len(data["holdings"])})

@app.post("/api/dividend")
def add_dividend():
    body = request.get_json(force=True)
    try:
        amount = float(body.get("amount", 0))
        shares = float(body.get("shares", 0))
        if amount <= 0 or shares <= 0:
            raise ValueError("Dividend per share and share count must be positive.")
        data = load_data()
        item = {
            "id": str(int(time.time() * 1000)),
            "symbol": body.get("symbol", "").strip().upper(),
            "amount": amount,
            "shares": shares,
            "pay_date": body.get("pay_date") or date.today().isoformat(),
            "currency": body.get("currency", "USD").upper(),
            "note": (body.get("note") or "Manually recorded").strip()[:100],
            "total": amount * shares
        }
        data["manual_dividends"].append(item)
        save_data(data)
        return jsonify({"ok": True, "dividend": item})
    except (ValueError, TypeError) as exc:
        return jsonify({"error": str(exc)}), 400

@app.delete("/api/dividend/<item_id>")
def delete_dividend(item_id):
    data = load_data()
    data["manual_dividends"] = [d for d in data["manual_dividends"] if d["id"] != item_id]
    save_data(data)
    return jsonify({"ok": True})

@app.get("/api/quote")
def quote():
    symbol = request.args.get("symbol", "").strip().upper()
    market = request.args.get("market", "US").upper()
    exchange = request.args.get("exchange", "NASDAQ" if market == "US" else "NSE").upper()
    try:
        provider_symbol = normalize_symbol(symbol, market, exchange)
        payload = api_get("quote", {"symbol": provider_symbol})
        return jsonify({"ok": True, "data": payload, "provider_symbol": provider_symbol, "fetched_at": datetime.utcnow().isoformat() + "Z"})
    except (RuntimeError, ValueError) as exc:
        return jsonify({"ok": False, "error": str(exc), "needs_key": not bool(API_KEY)}), 503

@app.get("/api/dividends")
def dividends():
    symbol = request.args.get("symbol", "").strip().upper()
    market = request.args.get("market", "US").upper()
    exchange = request.args.get("exchange", "NASDAQ" if market == "US" else "NSE").upper()
    try:
        provider_symbol = normalize_symbol(symbol, market, exchange)
        payload = api_get("dividends", {"symbol": provider_symbol, "range": "5y"})
        return jsonify({"ok": True, "data": payload, "provider_symbol": provider_symbol})
    except (RuntimeError, ValueError) as exc:
        return jsonify({"ok": False, "error": str(exc), "note": "Dividend endpoint access depends on your Twelve Data subscription."}), 503

@app.get("/api/market-status")
def market_status():
    return jsonify({"live_enabled": bool(API_KEY), "provider": "Twelve Data", "refresh_seconds": 60})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
