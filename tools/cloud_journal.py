"""Mechanical helpers for the cloud desk (the scheduled routine that keeps the team learning).

The routine's agent does the thinking (summary, desk call, lessons); this script does the
bookkeeping so the numbers are exact and the journal file stays well-formed.

Usage (from the repo root, after `pip install -r requirements.txt`):
  python tools/cloud_journal.py snapshot            # live watchlist snapshot as JSON
  python tools/cloud_journal.py grade               # grade open desk calls whose horizon has passed
  python tools/cloud_journal.py add entry.json      # append a journal entry (and its desk call)
  python tools/cloud_journal.py show                # print the last 3 entries, lessons and record

journal/journal.json shape:
  {"updated": iso, "entries": [...], "calls": [...], "lessons": [...]}
  entry: {"at", "session", "summary", "watchlist": [{"sym","price","chg_pct"}], "movers", "news": [{"title","source","url"}],
          "watch_next", "desk_call": {"ticker","stance","horizon_days","confidence","thesis"} | null}
  call:  {"id","date","ticker","stance","horizon_days","confidence","price_at_call","thesis","outcome","latest_price","return_pct","lesson_saved"}
  lesson:{"at","call_id","lesson"}
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yfinance as yf

ROOT = Path(__file__).resolve().parent.parent
JOURNAL = ROOT / "journal" / "journal.json"
WATCHLIST = ["NVDA", "SPY", "QQQ", "SMH", "AMD", "AVGO", "TSM", "^VIX"]
KEEP_ENTRIES, KEEP_CALLS, KEEP_LESSONS = 60, 120, 60


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load():
    if JOURNAL.exists():
        return json.loads(JOURNAL.read_text())
    return {"updated": None, "entries": [], "calls": [], "lessons": []}


def save(j):
    j["updated"] = now()
    j["entries"] = j["entries"][-KEEP_ENTRIES:]
    j["calls"] = j["calls"][-KEEP_CALLS:]
    j["lessons"] = j["lessons"][-KEEP_LESSONS:]
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL.write_text(json.dumps(j, indent=2) + "\n")


def last_price(sym):
    """Latest price and the prior session's close, both from daily history (fast_info's previous close can lag)."""
    closes = yf.Ticker(sym).history(period="7d", interval="1d", auto_adjust=False)["Close"].dropna()
    return float(closes.iloc[-1]), float(closes.iloc[-2])


def snapshot():
    rows = []
    for s in WATCHLIST:
        try:
            p, prev = last_price(s)
            rows.append({"sym": s, "price": round(p, 2), "chg_pct": round((p / prev - 1) * 100, 2)})
        except Exception as e:  # keep going; report the gap
            rows.append({"sym": s, "error": str(e)[:120]})
    return {"retrieved_utc": now(), "source": "Yahoo Finance via yfinance (may be delayed up to 15 minutes)", "watchlist": rows}


def grade():
    """Bullish is right above +2%, bearish right below -2%, neutral right within +/-5%."""
    j = load()
    graded = []
    for c in j["calls"]:
        if c.get("outcome") != "open":
            continue
        due = datetime.fromisoformat(c["date"]) + timedelta(days=int(c["horizon_days"]))
        try:
            px, _ = last_price(c["ticker"])
        except Exception:
            continue
        ret = (px / c["price_at_call"] - 1) * 100
        c["latest_price"], c["return_pct"] = round(px, 2), round(ret, 2)
        if datetime.now(timezone.utc) < due:
            continue
        right = ret > 2 if c["stance"] == "bullish" else ret < -2 if c["stance"] == "bearish" else abs(ret) <= 5
        c["outcome"] = "right" if right else "wrong"
        graded.append(c)
    save(j)
    done = [c for c in j["calls"] if c.get("outcome") in ("right", "wrong")]
    hits = sum(c["outcome"] == "right" for c in done)
    return {"newly_graded": graded, "record": {"graded": len(done), "right": hits, "hit_rate": round(hits / len(done), 3) if done else None},
            "need_lessons": [c for c in done if not c.get("lesson_saved")]}


def add(path):
    j = load()
    e = json.loads(Path(path).read_text())
    e.setdefault("at", now())
    j["entries"].append(e)
    call = e.get("desk_call")
    if call and call.get("ticker"):
        px, _ = last_price(call["ticker"])
        j["calls"].append({
            "id": "cloud_" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M"),
            "date": now(), "ticker": call["ticker"].upper(), "stance": call["stance"],
            "horizon_days": int(call.get("horizon_days", 5)), "confidence": int(call.get("confidence", 60)),
            "price_at_call": round(px, 2), "thesis": call.get("thesis", "")[:400],
            "outcome": "open", "latest_price": round(px, 2), "return_pct": 0.0, "lesson_saved": False,
        })
    for les in e.pop("new_lessons", []) or []:
        j["lessons"].append({"at": now(), "call_id": les.get("call_id"), "lesson": les["lesson"][:300]})
        for c in j["calls"]:
            if c["id"] == les.get("call_id"):
                c["lesson_saved"] = True
    save(j)
    return {"entries": len(j["entries"]), "calls": len(j["calls"]), "lessons": len(j["lessons"])}


def show():
    j = load()
    return {"updated": j["updated"], "last_entries": j["entries"][-3:], "lessons": j["lessons"][-10:],
            "open_calls": [c for c in j["calls"] if c["outcome"] == "open"]}


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "snapshot":
        out = snapshot()
    elif cmd == "grade":
        out = grade()
    elif cmd == "add" and len(sys.argv) == 3:
        out = add(sys.argv[2])
    elif cmd == "show":
        out = show()
    else:
        sys.exit(__doc__)
    print(json.dumps(out, indent=2, default=str))
