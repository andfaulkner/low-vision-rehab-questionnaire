#!/usr/bin/env python3
"""Validate a CSV of screening decisions (as subagents return them) against
the Lists tab and write them into the workbook through the screening-workbook
skill's set_cells.py.

    python3 -I apply_decisions.py analysis/screening/ta_ai_pass1.csv --target ai1            # dry run (default)
    python3 -I apply_decisions.py analysis/screening/ta_ai_pass1.csv --target ai1 --apply --export
    python3 -I apply_decisions.py analysis/screening/ta_ai_pass2.csv --target ai2 --apply --export
    python3 -I apply_decisions.py reviewer_ta.csv --target reviewer-ta --reviewer --apply --export
    python3 -I apply_decisions.py reviewer_ft.csv --target reviewer-ft --reviewer --apply --export

Input columns (header case does not matter; extra columns are ignored):
    id, decision, reason, rationale        for AI targets (rationale -> P or S, one line)
    id, decision, reason, notes            for reviewer targets (notes -> L, optional)
A "quote" column is appended to the rationale as: rationale | "quote".

Targets and the columns written:
    ai1          N, O, P   first AI pass (Suggested decision / reason / rationale)
    ai2          Q, R, S   second, independent AI pass
    reviewer-ta  H, I, L   the reviewer's title/abstract decision; needs --reviewer
    reviewer-ft  J, K, L   the reviewer's full-text decision; needs --reviewer

There is no AI full-text target on purpose: the workbook has no columns for
it. Keep AI full-text decisions in analysis/screening/ft_ai_decisions.csv and
compare them with agreement.py --b-file.

Checks, all of which stop the script with exit status 2 before anything is
written: decision not in the Lists tab for the stage (Maybe is refused at
full text), reason not spelled exactly as in Lists, Exclude without exactly
one reason, Include/Maybe with a reason, an ID that is not in the workbook,
an ID listed twice, a multi-line rationale. Near misses are reported with
the intended spelling.

By default this is a dry run: it prints every cell that would change and
writes nothing. --apply writes, --export regenerates the CSV exports too.
Writing H-L needs --reviewer, which asserts the reviewer dictated these exact
values; AI decisions never go there, because the Counts tab treats H-L as
the reviewer's decisions and compares them against N to measure how often
the reviewer overrode the AI.
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import screening_common as sc  # noqa: E402

TARGETS = {
    "ai1": {"cols": ("N", "O", "P"), "stage": "ta", "reviewer": False, "text": "rationale"},
    "ai2": {"cols": ("Q", "R", "S"), "stage": "ta", "reviewer": False, "text": "rationale"},
    "reviewer-ta": {"cols": ("H", "I", "L"), "stage": "ta", "reviewer": True, "text": "notes"},
    "reviewer-ft": {"cols": ("J", "K", "L"), "stage": "ft", "reviewer": True, "text": "notes"},
}


def one_line(s):
    return re.sub(r"\s+", " ", (s or "")).strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv", help="decisions CSV: id, decision, reason, rationale/notes[, quote]")
    ap.add_argument("--target", choices=sorted(TARGETS), required=True, help="which workbook columns receive the decisions")
    ap.add_argument("--xlsx", default=sc.DEFAULT_XLSX, help="workbook (default data/LVR_screening_sheet_2.xlsx)")
    ap.add_argument("--out", help="write the edited workbook here instead of in place (testing)")
    ap.add_argument("--apply", action="store_true", help="actually write; without it this is a dry run")
    ap.add_argument("--reviewer", action="store_true", help="the reviewer dictated these values (required for reviewer-* targets)")
    ap.add_argument("--export", action="store_true", help="regenerate the CSV exports after writing (passed to set_cells.py)")
    ap.add_argument("--keep-text", action="store_true", help="do not overwrite an existing rationale/notes cell when the CSV's is empty")
    ap.add_argument("--verbose", action="store_true", help="list every cell (passed to set_cells.py)")
    args = ap.parse_args()

    spec = TARGETS[args.target]
    if spec["reviewer"] and not args.reviewer:
        sc.die("target %s writes the reviewer's columns %s; pass --reviewer only if the reviewer stated these exact decisions. "
               "AI decisions belong in ai1 (N-P) or ai2 (Q-S)." % (args.target, "/".join(spec["cols"])), 2)
    if not spec["reviewer"] and args.reviewer:
        print("note: --reviewer is irrelevant for target %s (it writes %s)" % (args.target, "/".join(spec["cols"])), file=sys.stderr)
    if not os.path.isfile(args.xlsx):
        sc.die("workbook not found: %s" % args.xlsx)
    set_cells = os.path.join(sc.WORKBOOK_SCRIPTS, "set_cells.py")
    if not os.path.isfile(set_cells):
        sc.die("screening-workbook skill's set_cells.py not found at %s" % set_cells)

    try:
        t = sc.load_table(args.xlsx)
        fields, rows = sc.read_decisions_csv(args.csv)
    except (sc.ScreeningError, OSError) as e:
        sc.die(str(e))
    for needed in ("id", "decision"):
        if needed not in fields:
            sc.die("%s needs a column %r (has: %s)" % (args.csv, needed, ", ".join(fields.values())))
    if "reason" not in fields:
        print("note: no 'reason' column; every decision is checked as if its reason were blank", file=sys.stderr)
    text_key = spec["text"] if spec["text"] in fields else ("rationale" if "rationale" in fields else ("notes" if "notes" in fields else None))

    decisions_ok, reasons_ok = sc.allowed_values(t.lists, spec["stage"])
    ids_in_wb = {rid for rid, _ in t.records()}
    problems, seen, edits = [], set(), []
    for n, r in enumerate(rows, 2):
        rid_s = r.get("id", "").strip()
        where = "%s line %d" % (os.path.basename(args.csv), n)
        if not rid_s.isdigit():
            problems.append("%s: ID %r is not a number" % (where, rid_s))
            continue
        rid = int(rid_s)
        if rid in seen:
            problems.append("%s: ID %d listed twice" % (where, rid))
            continue
        seen.add(rid)
        if rid not in ids_in_wb:
            problems.append("%s: ID %d is not in the workbook" % (where, rid))
        dec = r.get("decision", "").strip()
        reason = r.get("reason", "").strip()
        if dec not in decisions_ok:
            hint = sc.nearest(dec, decisions_ok)
            extra = " (did you mean %r?)" % hint if hint else ""
            if dec == "Maybe" and spec["stage"] == "ft":
                extra = " (no Maybe at full text: decide Include or Exclude)"
            problems.append("%s: decision %r is not allowed at %s%s; allowed: %s" % (where, dec, spec["stage"], extra, " | ".join(decisions_ok)))
        if reason and reason not in reasons_ok:
            hint = sc.nearest(reason, reasons_ok)
            problems.append("%s: reason %r is not in Lists%s" % (where, reason, " (did you mean %r?)" % hint if hint else ""))
        if dec == "Exclude" and not reason:
            problems.append("%s: Exclude needs exactly one reason" % where)
        if dec in ("Include", "Maybe") and reason:
            problems.append("%s: %s must not carry a reason (%r); put the explanation in the rationale" % (where, dec, reason))
        text = one_line(r.get(text_key, "")) if text_key else ""
        if "quote" in fields and one_line(r.get("quote", "")):
            text = (text + ' | "' + one_line(r["quote"]) + '"') if text else '"' + one_line(r["quote"]) + '"'
        if text_key and "\n" in (r.get(text_key) or "").strip("\n"):
            print("note: %s: multi-line %s collapsed to one line" % (where, text_key), file=sys.stderr)
        dcol, rcol, tcol = spec["cols"]
        edits.append((rid, dcol, dec))
        edits.append((rid, rcol, reason))
        if text or not args.keep_text:
            edits.append((rid, tcol, text))
    if problems:
        for p in problems:
            print("refused: %s" % p, file=sys.stderr)
        print("error: %d problem(s) in %s; nothing written (Lists from %s)" % (len(problems), args.csv, t.lists_source), file=sys.stderr)
        sys.exit(2)
    if not edits:
        sc.die("no decisions in %s" % args.csv)

    tmpdir = tempfile.mkdtemp(prefix="apply_decisions_")
    edits_path = os.path.join(tmpdir, "edits.csv")
    import csv
    with open(edits_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["id", "col", "value"])
        w.writerows(edits)
    cmd = [sys.executable, "-I", set_cells, "--xlsx", args.xlsx, "--edits", edits_path]
    if spec["reviewer"]:
        cmd.append("--reviewer")
    if not args.apply:
        cmd.append("--dry-run")
    if args.out:
        cmd += ["--out", args.out]
    if args.export and args.apply:
        cmd.append("--export")
    if args.verbose:
        cmd.append("--verbose")
    print("%s: %d record(s) -> columns %s (%s)%s" % (
        "DRY RUN" if not args.apply else "WRITING", len(seen), "/".join(spec["cols"]), args.target,
        "" if args.apply else "; pass --apply to write"), file=sys.stderr)
    sys.stderr.flush()
    rc = subprocess.call(cmd)
    try:
        os.remove(edits_path)
        os.rmdir(tmpdir)
    except OSError:
        pass
    if rc == 0 and not spec["reviewer"]:
        print("These are AI suggestions in the grey columns; the reviewer decides in H-L, and the Methods must say AI assistance was used.", file=sys.stderr)
    sys.exit(rc)


if __name__ == "__main__":
    main()
