#!/usr/bin/env python3
"""Report which items of a filled PRISMA-style checklist are still blank.

The checklist is a Markdown file with one or more tables whose header row has a
column containing "Where reported" (the assets/ checklists have this shape).
An item counts as blank when that column is empty, a dash, a {placeholder},
or TBD/TODO. "N/A" with a reason counts as filled and is listed separately.

Exit status: 0 normally; 1 with --strict when any item is blank; 2 when a
file has no checklist table at all.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

BLANK_RE = re.compile(r"^\s*(?:[-–—]+|tbd|todo|\{[^}]*\}|\?+)?\s*$", re.IGNORECASE)
NA_RE = re.compile(r"^\s*n/?a\b", re.IGNORECASE)


def split_row(line: str) -> list[str]:
    cells = line.strip().strip("|").split("|")
    return [c.strip() for c in cells]


def parse_tables(text: str) -> list[dict]:
    """Return tables as {'title': ..., 'where_col': i, 'rows': [cells...]}."""
    tables, lines = [], text.splitlines()
    title = ""
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("#"):
            title = line.lstrip("#").strip()
        if line.lstrip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-{2,}", lines[i + 1]):
            header = split_row(line)
            where = next((k for k, h in enumerate(header) if "where reported" in h.lower()), None)
            i += 2
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                rows.append(split_row(lines[i]))
                i += 1
            if where is not None:
                tables.append({"title": title, "header": header, "where_col": where, "rows": rows})
            continue
        i += 1
    return tables


def status(path: Path, show_filled: bool) -> tuple[int, int, int]:
    text = path.read_text(encoding="utf-8")
    tables = parse_tables(text)
    if not tables:
        print(f"{path}: no table with a 'Where reported' column found")
        return 0, 0, -1
    blank = na = filled = 0
    print(f"== {path}")
    for t in tables:
        wc = t["where_col"]
        for cells in t["rows"]:
            if len(cells) <= wc:
                cells = cells + [""] * (wc + 1 - len(cells))
            item = cells[0]
            if not item or set(item) <= set("-: "):
                continue
            label = re.sub(r"\*+", "", cells[1])[:55] if len(cells) > 1 else ""
            where = re.sub(r"\*+", "", cells[wc])
            if BLANK_RE.match(where):
                blank += 1
                print(f"  BLANK  {item:<5} {label}")
            elif NA_RE.match(where):
                na += 1
                print(f"  N/A    {item:<5} {label}  -> {where}")
            else:
                filled += 1
                if show_filled:
                    print(f"  ok     {item:<5} {label}  -> {where}")
    total = blank + na + filled
    print(f"  {filled} of {total} items filled, {na} marked N/A, {blank} still blank")
    return blank, total, na


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("checklists", nargs="+", type=Path, help="filled checklist Markdown file(s)")
    p.add_argument("--show-filled", action="store_true", help="also list the filled items")
    p.add_argument("--strict", action="store_true", help="exit 1 if any item is still blank")
    a = p.parse_args(argv)
    total_blank, bad_file = 0, False
    for path in a.checklists:
        if not path.exists():
            print(f"{path}: not found", file=sys.stderr)
            bad_file = True
            continue
        blank, total, na = status(path, a.show_filled)
        if na < 0:
            bad_file = True
        total_blank += blank
    if bad_file:
        return 2
    return 1 if (a.strict and total_blank) else 0


if __name__ == "__main__":
    sys.exit(main())
