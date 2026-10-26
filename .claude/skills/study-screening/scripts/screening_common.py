"""Shared helpers for the study-screening scripts (standard library only).

Loads the Screening tab either from the workbook (through the
screening-workbook skill's lvrwb module, so the x14 validations and cached
Counts are never touched) or from a CSV export (whose first line is the sheet
name), resolves columns by header text or letter, and reads the Lists tab so
that decisions and reasons can be validated against the exact strings the
Counts formulas look for.
"""

import csv
import os
import re
import sys

sys.dont_write_bytecode = True

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_DIR = os.path.dirname(SKILL_DIR)
REPO_ROOT = os.path.dirname(os.path.dirname(SKILLS_DIR))
WORKBOOK_SCRIPTS = os.path.join(SKILLS_DIR, "screening-workbook", "scripts")
DEFAULT_XLSX = os.path.join(REPO_ROOT, "data", "LVR_screening_sheet_2.xlsx")
DEFAULT_TEXT_DIR = os.path.join(REPO_ROOT, "data", "articles_text")
DEFAULT_PDF_DIR = os.path.join(REPO_ROOT, "data", "articles")
SCREENING = "Screening"

# Column letter -> header text on the Screening tab, as the workbook has it.
HEADERS = {
    "A": "ID", "B": "Year", "C": "Authors", "D": "Title", "E": "Journal", "F": "DOI link",
    "G": "Abstract", "H": "Title/abstract decision", "I": "Exclusion reason (T/A)",
    "J": "Full-text decision", "K": "Exclusion reason (FT)", "L": "Notes", "M": "Zotero key",
    "N": "Suggested decision (AI)", "O": "Suggested reason (AI)", "P": "AI rationale",
    "Q": "Independent T/A decision (AI)", "R": "Independent exclusion reason (AI)",
    "S": "Independent rationale (AI)",
}
REASON_FOR_DECISION = {"H": "I", "J": "K", "N": "O", "Q": "R"}
REVIEWER_COLS = ("H", "I", "J", "K", "L")

# Fallback only: the Lists tab is the authority. Used when neither the xlsx
# nor a Lists CSV can be found, and the scripts say so when they fall back.
FALLBACK_LISTS = {
    "A": ["Include", "Exclude", "Maybe"],
    "B": ["Include", "Exclude"],
    "C": ["Wrong population (not adults)", "No questionnaire/screening item",
          "No accuracy/validation data", "Intervention study only",
          "Not about low vision/visual function", "Review/opinion/editorial",
          "Conference abstract only", "Language (not English/French)",
          "Full text not available", "Other (see notes)"],
}


class ScreeningError(Exception):
    pass


def die(msg, code=1):
    print("error: %s" % msg, file=sys.stderr)
    sys.exit(code)


def nice_path(path):
    """Repo-relative when the file is inside the repo, else the absolute path."""
    rel = os.path.relpath(path, REPO_ROOT)
    return rel if not rel.startswith("..") else os.path.abspath(path)


def col_letter(i):
    s = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


def import_lvrwb():
    """The screening-workbook helper, if it is installed next to this skill."""
    if not os.path.isdir(WORKBOOK_SCRIPTS):
        raise ScreeningError("screening-workbook skill not found at %s" % WORKBOOK_SCRIPTS)
    if WORKBOOK_SCRIPTS not in sys.path:
        sys.path.insert(0, WORKBOOK_SCRIPTS)
    import lvrwb  # noqa: E402
    return lvrwb


class Table:
    """Header row plus data rows, all strings, with column lookup by header or letter."""

    def __init__(self, header, rows, source, lists, lists_source):
        self.header = header
        self.rows = rows
        self.source = source
        self.lists = lists
        self.lists_source = lists_source
        self.hyperlinks = {}

    def col_index(self, name):
        """Index of a column given its header text (exact, then case-insensitive) or its letter."""
        if name is None:
            return None
        name = name.strip()
        if name in self.header:
            return self.header.index(name)
        low = [h.strip().casefold() for h in self.header]
        if name.casefold() in low:
            return low.index(name.casefold())
        if re.fullmatch(r"[A-Za-z]{1,2}", name):
            idx = 0
            for ch in name.upper():
                idx = idx * 26 + (ord(ch) - 64)
            idx -= 1
            if idx < len(self.header):
                return idx
        raise ScreeningError("no column %r; headers are: %s" % (name, " | ".join(self.header)))

    def letter_of(self, name):
        return col_letter(self.col_index(name))

    def get(self, row, name):
        i = self.col_index(name)
        return (row[i] if i < len(row) else "").strip()

    def records(self):
        """Rows with a numeric ID, as (id:int, row)."""
        i = self.col_index("ID")
        out = []
        for r in self.rows:
            v = (r[i] if i < len(r) else "").strip()
            if re.fullmatch(r"\d+(\.0+)?", v):
                out.append((int(float(v)), r))
        return out


def _read_lists_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    out = {}
    for r in rows[1:]:
        for i, v in enumerate(r):
            if v.strip():
                out.setdefault(col_letter(i), []).append(v.strip())
    return out


def load_table(path=None, lists_path=None):
    """Load the Screening tab from an .xlsx (via lvrwb) or a CSV export."""
    path = path or DEFAULT_XLSX
    if not os.path.isfile(path):
        raise ScreeningError("not found: %s" % path)
    if path.lower().endswith(".xlsx"):
        lvrwb = import_lvrwb()
        wb = lvrwb.Workbook(path)
        grid = wb.grid(SCREENING)
        header = [str(h or "") for h in grid[0]]
        rows = [[str(v or "") for v in r] for r in grid[1:]]
        lists = wb.lists()
        t = Table(header, rows, path, lists, "%s (Lists tab)" % nice_path(path))
        t.hyperlinks = wb.hyperlinks(SCREENING)
        return t
    with open(path, newline="", encoding="utf-8") as f:
        raw = list(csv.reader(f))
    if not raw:
        raise ScreeningError("%s is empty" % path)
    if len(raw) > 1 and len([c for c in raw[0] if c.strip()]) == 1 and "ID" not in raw[0]:
        raw = raw[1:]  # the export's first line is the sheet name
    header = [h.strip() for h in raw[0]]
    if "ID" not in header:
        raise ScreeningError("%s has no ID column in its header row" % path)
    rows = [r + [""] * (len(header) - len(r)) for r in raw[1:]]
    lists, src = None, None
    cands = [lists_path] if lists_path else []
    here = os.path.dirname(os.path.abspath(path))
    stem = re.sub(r"_Screening$", "", os.path.splitext(os.path.basename(path))[0])
    cands.append(os.path.join(here, stem + "_Lists.csv"))
    cands.extend(os.path.join(here, f) for f in sorted(os.listdir(here)) if f.endswith("_Lists.csv"))
    cands.append(os.path.join(REPO_ROOT, "data", "LVR_screening_sheet_2_Lists.csv"))
    for c in cands:
        if c and os.path.isfile(c):
            lists, src = _read_lists_csv(c), nice_path(c)
            break
    if lists is None:
        lists, src = FALLBACK_LISTS, "built-in fallback (no Lists tab or Lists CSV found)"
    return Table(header, rows, path, lists, src)


def allowed_values(lists, stage):
    """(decisions, reasons) allowed at a stage: 'ta' or 'ft'."""
    key = "A" if stage == "ta" else "B"
    decisions = lists.get(key) or FALLBACK_LISTS[key]
    reasons = lists.get("C") or FALLBACK_LISTS["C"]
    return list(decisions), list(reasons)


def nearest(value, allowed):
    """The allowed string a near-miss (case, spacing, punctuation) was meant to be, or None."""
    v = value.strip().casefold()
    for a in allowed:
        if a.strip().casefold() == v:
            return a
    v2 = re.sub(r"[^a-z0-9]+", "", v)
    for a in allowed:
        if re.sub(r"[^a-z0-9]+", "", a.casefold()) == v2:
            return a
    return None


def read_decisions_csv(path):
    """A subagent or second-reviewer CSV: columns id, decision, reason, rationale/notes, quote
    (header case does not matter). Returns (fieldnames lowercased -> original, rows lowercased)."""
    with open(path, newline="", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        if not rd.fieldnames:
            raise ScreeningError("%s has no header" % path)
        fields = {h.strip().casefold(): h for h in rd.fieldnames}
        rows = [{(k or "").strip().casefold(): (v or "") for k, v in r.items()} for r in rd]
    return fields, rows
