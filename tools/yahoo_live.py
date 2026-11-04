"""Live market data from Yahoo Finance for the Financial Analysis Team.

Usage:
  .venv/bin/python tools/yahoo_live.py quote NVDA
  .venv/bin/python tools/yahoo_live.py expirations NVDA
  .venv/bin/python tools/yahoo_live.py puts NVDA 2026-12-18 [--near 10]
  .venv/bin/python tools/yahoo_live.py calls NVDA 2026-12-18 [--near 10]
  .venv/bin/python tools/yahoo_live.py history NVDA 1y [1d]
  .venv/bin/python tools/yahoo_live.py hv NVDA            # realized volatility

Every output includes the retrieval timestamp so consumers can judge freshness.
"""
import json
import math
import sys
from datetime import datetime, timezone

import yfinance as yf


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def clean(v):
    if v is None:
        return None
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    if hasattr(v, "item"):
        return clean(v.item())
    if hasattr(v, "isoformat"):
        return v.isoformat()
    return v


def quote(sym):
    t = yf.Ticker(sym)
    info = t.info
    fields = [
        "shortName", "currency", "exchange", "marketState",
        "regularMarketPrice", "regularMarketChange", "regularMarketChangePercent",
        "regularMarketTime", "regularMarketOpen", "regularMarketDayHigh",
        "regularMarketDayLow", "regularMarketVolume", "regularMarketPreviousClose",
        "preMarketPrice", "preMarketTime", "postMarketPrice", "postMarketTime",
        "bid", "ask", "bidSize", "askSize",
        "fiftyTwoWeekLow", "fiftyTwoWeekHigh", "fiftyDayAverage", "twoHundredDayAverage",
        "averageVolume", "marketCap", "sharesOutstanding", "beta",
        "trailingPE", "forwardPE", "dividendYield",
        "earningsTimestamp", "earningsTimestampStart", "earningsTimestampEnd",
        "exchangeDataDelayedBy",
    ]
    out = {k: clean(info.get(k)) for k in fields}
    for k in ("regularMarketTime", "preMarketTime", "postMarketTime",
              "earningsTimestamp", "earningsTimestampStart", "earningsTimestampEnd"):
        if isinstance(out.get(k), (int, float)):
            out[k] = datetime.fromtimestamp(out[k], timezone.utc).isoformat()
    return {"symbol": sym, "retrieved_utc": now(), "source": "Yahoo Finance", "quote": out}


def expirations(sym):
    return {"symbol": sym, "retrieved_utc": now(), "expirations": list(yf.Ticker(sym).options)}


def chain(sym, expiry, side, near=None):
    t = yf.Ticker(sym)
    spot = t.fast_info["last_price"]
    oc = t.option_chain(expiry)
    df = oc.puts if side == "puts" else oc.calls
    cols = ["contractSymbol", "strike", "lastPrice", "bid", "ask", "change",
            "volume", "openInterest", "impliedVolatility", "inTheMoney", "lastTradeDate"]
    df = df[cols].copy()
    if near:
        df = df.iloc[(df["strike"] - spot).abs().argsort()[: int(near)]].sort_values("strike")
    rows = [{k: clean(v) for k, v in r.items()} for r in df.to_dict("records")]
    for r in rows:
        if r["bid"] is not None and r["ask"] is not None and r["ask"] > 0:
            r["mid"] = round((r["bid"] + r["ask"]) / 2, 4)
    days = (datetime.strptime(expiry, "%Y-%m-%d").date() - datetime.now(timezone.utc).date()).days
    return {"symbol": sym, "retrieved_utc": now(), "spot": clean(spot), "expiry": expiry,
            "days_to_expiry": days, "side": side, "contracts": rows}


def history(sym, period="1y", interval="1d"):
    df = yf.Ticker(sym).history(period=period, interval=interval, auto_adjust=True)
    rows = [{"date": d.isoformat(), "open": clean(r.Open), "high": clean(r.High),
             "low": clean(r.Low), "close": clean(r.Close), "volume": clean(r.Volume)}
            for d, r in df.iterrows()]
    return {"symbol": sym, "retrieved_utc": now(), "period": period, "interval": interval,
            "rows": rows}


def hv(sym):
    df = yf.Ticker(sym).history(period="2y", auto_adjust=True)
    r = (df["Close"] / df["Close"].shift(1)).apply(math.log).dropna()
    out = {}
    for w in (20, 60, 120, 252):
        if len(r) >= w:
            out[f"hv_{w}d_annualized"] = round(float(r.tail(w).std() * math.sqrt(252)), 4)
    return {"symbol": sym, "retrieved_utc": now(), "last_close": clean(df["Close"].iloc[-1]),
            "realized_volatility": out}


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    cmd, sym = argv[0], argv[1].upper()
    near = None
    if "--near" in argv:
        near = argv[argv.index("--near") + 1]
    if cmd == "quote":
        res = quote(sym)
    elif cmd == "expirations":
        res = expirations(sym)
    elif cmd in ("puts", "calls"):
        res = chain(sym, argv[2], cmd, near)
    elif cmd == "history":
        res = history(sym, *argv[2:4])
    elif cmd == "hv":
        res = hv(sym)
    else:
        sys.exit(__doc__)
    print(json.dumps(res, indent=2, default=str))


if __name__ == "__main__":
    main(sys.argv[1:])
