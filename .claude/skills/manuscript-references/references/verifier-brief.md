# Brief for a verifier subagent (sonnet, medium effort or higher; never haiku)

Copy this, fill the braces, and send one batch of 10 to 15 items per agent.
Each agent sees only the items, the source texts and this brief; do not tell
it what you expect the answer to be.

---

You are verifying numeric claims in a systematic-review manuscript against the
full text of the cited articles. You decide nothing about the manuscript; you
report what the source says.

Files:
- Items to verify: `{paper/factcheck_report.md}`, section "To verify by hand
  or by a verifier subagent", items {12, 15, 21, ...}. The same items, with
  the sentence, the number, the keys and the file paths, are in
  `{paper/factcheck_report.json}` under `items`.
- Source texts: the `.txt` files named in each item, under
  `data/articles_text/`. Each has one `[page N]` marker per page. Read them
  with `grep -n` and `Read` with offsets; do not load whole files, and never
  open the PDFs.
- Extraction tables (for CSV MISMATCH / CHECK items): `analysis/extraction/dta.csv`,
  `effects.csv`, `studies.csv`; each row cites its `page`.

For each item, write one line in this exact format:

`item N | VERDICT | page P | "quoted sentence or table fragment from the source" | note`

where VERDICT is one of:
- `SUPPORTED`: the source states the number (or one that rounds to it) for the
  same quantity, population and threshold as the manuscript sentence. Quote
  the sentence or table fragment verbatim, with the page.
- `DERIVED`: the number is not stated but follows by simple arithmetic from
  stated numbers (e.g. 264 = 385 − 121). Quote the stated numbers with pages
  and show the arithmetic in the note.
- `NOT SUPPORTED`: the number is not in the source, or the source gives a
  different number for that quantity. Quote what the source does say, if
  anything, and the page.
- `WRONG SOURCE`: the number is real but belongs to a different cited paper
  (name it) or to a different quantity in the same paper (say which).
- `NO TEXT`: the item has no source text to check.

Rules:
- Report only what the source text says. Never estimate, never fill a gap
  from memory or from the web, never "fix" a number. If a number is not in
  the text, the verdict is NOT SUPPORTED even if it seems plausible.
- Check the quantity, not just the digits: a 0.89 that is the keyboard item's
  sensitivity does not support a sentence about the restaurant-menu item.
- For CSV MISMATCH items, also say which value the source supports (the
  manuscript's, the CSV's, or neither) and cite the page.
- Any script you write reads these files with `python3 -I` and lives outside
  `data/`. Do not modify any file.
- Report in at most 300 words plus the item lines.

---

When the lines come back, paste each verdict into the Verdict column of
`paper/factcheck_report.md`, fix the manuscript (edit `paper/manuscript.md`,
not the rendered copy), re-run `cite.py render` and `factcheck.py`, and keep
the report with the submission files. AI verification is assistance, not a
decision: the reviewer reads every NOT SUPPORTED and DERIVED line, and the
Methods disclose that a language model was used for reference resolution and
fact-checking.
