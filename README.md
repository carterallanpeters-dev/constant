# Financial Analysis Team

Nine Claude Code subagents, each with a 1990s trading-floor personality, that work as a pipeline to research and quantify a stock or options question.

| # | Member | File | Role |
|---|--------|------|------|
| 0 | Live Pricing Desk | `.claude/agents/fin-live-pricing.md` | Pulls live quotes, options chains, implied and realized volatility from Yahoo Finance (`tools/yahoo_live.py`); the team's single source for live prices |
| 1 | Source Researcher | `.claude/agents/fin-source-researcher.md` | Cross-references trusted public sources (SEC EDGAR, company IR, exchanges, Reuters/Bloomberg/WSJ, etc.) into a verified fact sheet |
| 2 | Market Historian | `.claude/agents/fin-market-historian.md` | Price history, volatility, drawdowns, earnings reactions, valuation history, market-cycle analogues |
| 3 | Fundamental Analyst | `.claude/agents/fin-fundamental-analyst.md` | Exact numbers from earnings reports and filings: margins, cash flow, DCF, multiples, and options math (Greeks, breakevens, probabilities) |
| 4 | Peer Comps | `.claude/agents/fin-peer-comps.md` | Compares the stock with public peers and sector ETFs, then briefs The Skeptic and The Optimist before they give their opinions |
| 5 | The Skeptic | `.claude/agents/fin-skeptic.md` | Brutally honest opinion on the findings: attacks weak assumptions, sends challenges back to teammates, and questions what you actually want |
| 6 | The Optimist | `.claude/agents/fin-optimist.md` | Evidence-based bull case: upside, catalysts, where the upside ends; debates The Skeptic and flags upside risk to bearish ideas |
| 7 | Presenter / Statistician | `.claude/agents/fin-presenter.md` | Reconciles the reports into one briefing with scenarios, probabilities, expected value, risks, and data-quality notes |
| 8 | The Closer | `.claude/agents/fin-closer.md` | Speaks last: the Desk Call on the evidence plus a pre-trade checklist; logs every call in `track-record/`, grades it later and saves lessons from misses |

```
Live Pricing Desk ─┐                          ┌─ price refresh ─┐
Source Researcher ─┴─► Market Historian ──────┤                 ├─► Presenter ──► Briefing
                    └─► Fundamental Analyst ──┘                 │
                                   ▲──── PRICE CHANGE recompute ┘
```

Setup (already done in this folder): `python3 -m venv .venv && .venv/bin/pip install yfinance openpyxl`

Excel reports: ask the Presenter for one and it builds an `.xlsx` with `tools/excel_report.py` (or, in the chat page, a Download button).

## Usage

Ask in a Claude Code session opened in this folder:

```
/financial-analysis-team What would a put on NVDA look like right now?
```

Reports are saved under `reports/<TICKER>-<date>/`.

There is also a chat page for talking to the team directly: https://claude.ai/artifact/RCrVsqzY4zGtKvMtTmVG7F (source: `team-chat.html`). Open it in the Claude desktop app for live Yahoo Finance prices.

## Limits

- Live prices come from Yahoo Finance's unofficial API (via `yfinance`): quotes may be delayed up to ~15 minutes, and Yahoo can rate-limit or change the API. A broker's quote is authoritative.
- The team produces research and a Desk Call on the evidence, not personalized investment advice: no buy/sell instructions, no position sizing, and it never places trades.

## Cloud desk (runs while your laptop is closed)

A scheduled Claude Code routine runs in Anthropic's cloud on weekdays at 9:30am, 12:30pm and 3:30pm Chicago time
(cron `30 15,18,21 * * 1-5`, UTC). Each run follows `cloud-desk/PROMPT.md`:

1. Grades past cloud desk calls against live prices (`tools/cloud_journal.py grade`).
2. Snapshots the watchlist (`tools/cloud_journal.py snapshot`) and checks the news behind big moves.
3. Writes a journal entry, at most one desk call, and lessons for graded calls (`tools/cloud_journal.py add`).
4. Commits and pushes `journal/journal.json` and `journal/latest.md`.

The garage page reads `journal/journal.json` from this repo (raw GitHub URL in `CLOUD_JOURNAL_URL` in `team-chat.html`),
so the team catches you up on what happened while you were away. Note: the bots don't retrain; they read this growing journal.
