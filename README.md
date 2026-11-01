# ASSASSIN'S LEDGER

A cinematic Assassin's Creed-inspired portfolio and dividend tracker for Indian (NSE/BSE) and US (NASDAQ/NYSE) equities.

## Features
- Intro / "Leap of Faith" landing screen. Click the original Assassin-inspired insignia to enter the ledger.
- Portfolio holdings with quantity, average buy price, live quote, market value, cost basis, and unrealized P/L.
- Indian and US market support. Indian symbols are sent to Twelve Data as `SYMBOL:NSE` or `SYMBOL:BSE`; US symbols are sent as tickers.
- Dividend log with manual entry, estimated income, and provider dividend history when the account has access.
- Market watchlist, search, allocation view, and portfolio summary.
- Local JSON persistence for this starter build.
- Responsive layout and motion effects; reduced-motion preference respected.

## Run locally
1. Install Python 3.10+.
2. In this folder, create and activate a virtual environment:
   - macOS/Linux: `python3 -m venv .venv && source .venv/bin/activate`
   - Windows: `py -m venv .venv && .venv\\Scripts\\activate`
3. Install packages: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env`, then set `TWELVE_DATA_API_KEY`. The app reads environment variables; to load `.env` automatically, export the variable in your shell or add `python-dotenv` and `load_dotenv()`.
5. Start: `python app.py`
6. Open http://127.0.0.1:5000

Example macOS/Linux:
```bash
export TWELVE_DATA_API_KEY="your_key_here"
python app.py
```

## Live data provider
This starter uses Twelve Data REST endpoints:
- `/quote` for latest quote fields.
- `/dividends` for historical dividend events.

Create an API key at https://twelvedata.com/. Market coverage, quote delay/real-time entitlement, API credits, and endpoint availability depend on your plan and exchange licensing. The Twelve Data documentation notes that the dividends endpoint costs 20 credits per symbol and is only available on eligible plans; if unavailable, use the manual dividend log in this app.

References:
- https://twelvedata.com/docs/markets/market-state
- https://twelvedata.com/docs/momentum-indicators
- https://support.twelvedata.com/en/articles/5620512-how-to-create-a-request

## Deploy on Render
- Push the folder contents to a GitHub repository.
- Create a Render **Web Service** from that repo.
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`
- Add environment variable `TWELVE_DATA_API_KEY` with your key.
- For durable holdings/dividend records, configure a persistent disk and set `DATA_DIR` to its mount path, or replace the JSON store with a managed database. The free instance filesystem is ephemeral; do not rely on it for long-term records.

## Important
- This is an educational portfolio tracker, not a broker, trading system, tax tool, or investment recommendation.
- Quote data may be delayed and may not be entitled for every exchange. "Live" means refreshed from the connected provider when available; this is not a guaranteed tick-by-tick stream.
- Dividend amounts, dates, and currencies must be checked against issuer/exchange records. Provider dividend coverage can vary.
- Never commit your API key or `.env` file to GitHub.
