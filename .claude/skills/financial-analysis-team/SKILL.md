---
name: financial-analysis-team
description: Run the Financial Analysis Team (Live Pricing, Source Researcher, Market Historian, Fundamental Analyst, Peer Comps, Skeptic, Optimist, Presenter, Closer) on a stock question, e.g. "/financial-analysis-team Should I consider a put on NVDA?" Use whenever the user asks the financial analysis team about a stock, ETF, or options position.
---

# Financial Analysis Team

Coordinate four subagents to answer the user's question: $ARGUMENTS

## Workflow

1. **Clarify the question** only if something essential is missing and can't be defaulted. For an options question, useful details are strike, expiration, and whether the put is a hedge on shares they own or a standalone bearish position. If not given, default to analyzing an at-the-money put and a ~10% out-of-the-money put at roughly 30 and 90 days out, and say you did so.
2. **Stage 1 — in parallel.** Launch `fin-live-pricing` (to produce `reports/<TICKER>-<date>/0-price-sheet.md`) and `fin-source-researcher` (to produce `1-fact-sheet.md`) in the same message, each given the ticker and the question.
3. **Stage 2 — in parallel.** Launch `fin-market-historian` and `fin-fundamental-analyst` in the same message, each given the price sheet, the fact sheet, and the user's question (tell the analyst to include the options section if the question involves options). Save outputs to `2-history.md` and `3-fundamentals.md`.
4. **Price check.** Relay any pricing questions the members raised to `fin-live-pricing` (continue the same agent with SendMessage when available) and ask it to refresh spot and the relevant option quotes. If it reports **PRICE CHANGE**, send the new numbers back to the Fundamental Analyst to recompute the affected options math before moving on.
5. **Stage 3a — Peer Comps.** Launch `fin-peer-comps` with the price sheet, all reports, and the question. Save to `4-peer-comps.md`. This must finish before Stage 3b: the Skeptic and the Optimist hear from Peer Comps before they give their opinions.
6. **Stage 3b — The Skeptic and The Optimist, in parallel.** Launch `fin-skeptic` and `fin-optimist` in the same message, each with the price sheet, all reports, the question, the full Peer Comps report, and their own briefing ("Briefing for The Skeptic" or "Briefing for The Optimist"), presented as a message from Peer Comps. Tell each to react to that briefing explicitly: agree, push back, or say how it changed their read. Save to `5-skeptic.md` and `5-optimist.md`. Then:
   - Route each item under the Skeptic's "Challenges for the team" to the named member (continue that agent with SendMessage when available) and collect their answers. A member either defends the number with evidence or revises it.
   - Send the Skeptic's critique to the Optimist and the Optimist's bull case to the Skeptic for one round of rebuttal each. Append the rebuttals to their files.
7. **Stage 4 — Presenter.** Launch `fin-presenter` with the price sheet, its refresh, all reports, the Peer Comps table, both opinion pieces with their rebuttals, and the teammates' answers to the Skeptic's challenges. Save to `6-briefing.md`. The briefing must include a "Bull vs. bear" section that keeps each side's opinion and confidence intact. The Presenter then weighs both against the statistics and doesn't average them away.
8. **Stage 5 — The Closer.** Launch `fin-closer` with the briefing, both opinion pieces, the Peer Comps report and the price sheet. It grades past calls in `track-record/`, applies saved lessons, makes the Desk Call and logs it. Save to `7-desk-call.md`.
9. **Deliver.** Show the user the Presenter's briefing (bottom line, key tables, scenario/probability table, risks, disclaimer), the Skeptic's questions for them, and the Closer's Desk Call with its track-record check. State the time the prices were retrieved, and link the report folder.

## Live pricing is the single source of truth

Any live number in any report (spot, bid/ask, option premium, implied volatility, realized volatility) must come from the Live Pricing Desk's price sheet or one of its refreshes, quoted with its timestamp. If a member's web research shows a different price, the price sheet wins, and the difference is noted as a timing gap. Subagents can't message each other directly, so the coordinator (you) relays every question and answer between the members and the pricing desk.

If the custom agent types aren't registered in the current session, run each stage with a `general-purpose` agent and paste that member's definition from `.claude/agents/<name>.md` into its prompt.

## Rules

- The team gives research and quantified analysis, not personalized investment advice: no "buy/sell this," no position sizing.
- Every number must trace to a source or a shown calculation. Flag stale or single-source data.
- Never place trades or interact with brokerage accounts.
