"""Build an Excel report for the Financial Analysis Team from a JSON spec.

Usage:
  .venv/bin/python tools/excel_report.py spec.json reports/NVDA-2026-11-04/NVDA-report.xlsx

Spec:
  {
    "title": "NVDA put analysis",
    "summary": "2-4 sentence bottom line",
    "sources": "Yahoo Finance 2026-11-04 16:32 ET; NVIDIA 10-Q ...",
    "sheets": [
      {"name": "Options", "columns": ["Strike", "Mid", "IV"],
       "rows": [[195, 8.10, 0.46], [200, 10.18, 0.448]],
       "formats": {"IV": "0.0%", "Mid": "$#,##0.00"},
       "notes": "Delayed 15 minutes."}
    ]
  }

An About sheet (title, summary, sources, date, disclaimer) is added first.
"""
import json
import re
import sys
from datetime import datetime

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

DISCLAIMER = ("Educational research, not investment advice. Quotes from Yahoo Finance can be "
              "delayed up to 15 minutes. Options can lose 100% of the premium.")
HEADER_FILL = PatternFill("solid", fgColor="142033")
HEADER_FONT = Font(bold=True, color="FFFFFF")


def sheet_name(name, used):
    base = re.sub(r"[\\/?*\[\]:]", " ", str(name)).strip()[:31] or "Sheet"
    candidate, n = base, 2
    while candidate.lower() in used:
        candidate = f"{base[:28]} {n}"
        n += 1
    used.add(candidate.lower())
    return candidate


def number(v):
    if isinstance(v, str) and re.fullmatch(r"-?\d+(\.\d+)?", v.strip()):
        return float(v) if "." in v else int(v)
    return v


def build(spec, out_path):
    wb = Workbook()
    about = wb.active
    about.title = "About"
    used = {"about"}
    about["A1"] = spec.get("title", "Financial Analysis Team report")
    about["A1"].font = Font(bold=True, size=16)
    rows = [("Summary", spec.get("summary", "")),
            ("Sources", spec.get("sources", "")),
            ("Created", datetime.now().strftime("%Y-%m-%d %H:%M")),
            ("Prepared by", "Financial Analysis Team (Anchor Annie)"),
            ("", ""),
            ("Disclaimer", DISCLAIMER)]
    for i, (k, v) in enumerate(rows, start=3):
        about.cell(row=i, column=1, value=k).font = Font(bold=True)
        about.cell(row=i, column=2, value=v).alignment = Alignment(wrap_text=True, vertical="top")
    about.column_dimensions["A"].width = 14
    about.column_dimensions["B"].width = 100

    for s in spec.get("sheets", [])[:12]:
        ws = wb.create_sheet(sheet_name(s.get("name", "Sheet"), used))
        cols = [str(c) for c in s.get("columns", [])]
        if cols:
            ws.append(cols)
            for cell in ws[1]:
                cell.fill, cell.font = HEADER_FILL, HEADER_FONT
            ws.freeze_panes = "A2"
        for r in s.get("rows", []):
            ws.append([number(v) for v in (r if isinstance(r, list) else [r])])
        for col_name, fmt in (s.get("formats") or {}).items():
            if col_name in cols:
                idx = cols.index(col_name) + 1
                for row in ws.iter_rows(min_row=2, min_col=idx, max_col=idx):
                    row[0].number_format = fmt
        for idx in range(1, ws.max_column + 1):
            letter = get_column_letter(idx)
            width = max((len(str(c.value)) for c in ws[letter] if c.value is not None), default=8)
            ws.column_dimensions[letter].width = min(45, max(10, width + 2))
        if s.get("notes"):
            ws.append([])
            ws.append([f"Notes: {s['notes']}"])
    wb.save(out_path)
    return out_path


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    with open(sys.argv[1]) as f:
        print("Saved", build(json.load(f), sys.argv[2]))
