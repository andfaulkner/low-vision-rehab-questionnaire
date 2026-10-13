---
name: pdf-to-text
description: Cheaply convert PDFs (e.g. the articles in data/articles/) into plain .txt files with a script, so they can be grepped and read in parts instead of loading whole PDFs into context. Repairs words that PDF extraction runs together. Use when asked to convert, extract text from, OCR, or read/search the full text of one or more PDFs, or when extracted text has words jammed together.
---

# PDF to text

Do everything with the script. Don't open PDFs with the Read tool to extract text, because that is far more expensive than reading the `.txt`.

```bash
.claude/skills/pdf-to-text/scripts/pdf2txt.sh [-o OUTDIR] [-f] [-n] [-r] [-e auto|pdftotext|pdfkit] PATH...
```

- `PATH` is any mix of PDF files and directories (searched recursively).
- By default each `foo.pdf` gets a `foo.txt` next to it. Use `-o DIR` to write the text files somewhere else instead (e.g. the scratchpad for one-off reads).
- It's incremental: a PDF whose `.txt` is already newer than it is skipped. Use `-f` to force re-conversion. Re-converting is always safe, because it starts again from the PDF and never re-repairs old text.
- Scanned PDFs (almost no text layer) are OCR'd automatically with macOS Vision. This takes about 1s per page, and the first use compiles a helper into `~/.cache/pdf-to-text/`. Use `-n` to skip OCR.

## Run-together words

PDFs often have no real space characters, so extractors guess where words break. Sometimes they guess wrong ("Weanalyzeddatafrom385adults"), and then grep misses those phrases. The script deals with this in three layers, and you don't need to do anything by hand:

1. **Better extractor.** It uses poppler's `pdftotext` and installs poppler if it's missing (Homebrew, or apt/dnf with passwordless sudo). macOS PDFKit is only a fallback, because it runs about 12× more words together.
2. **Repair.** `scripts/fixspaces.py` splits glued words, adds missing spaces after punctuation ("services.From"), and splits a surname glued to its initials ("MassofRW,"). It learns its vocabulary from the converted papers and every other `.txt` in the same folder, so terms like "logMAR" and "VA" count as words. It only splits a word when every piece is a known word and the glue is evident, so names, compounds and non-English words are left alone. Use `-r` to turn the repair off.
3. **Second engine.** A file that is still badly run together is re-extracted with the other engine, and the cleaner result is kept.

To preview what the repair would change without editing anything:

```bash
python3 -I .claude/skills/pdf-to-text/scripts/fixspaces.py --dry-run --lexicon DIR FILE.txt
```

## Output

The script prints one summary line. It prints extra lines only for files that need attention:

- `FAILED (unreadable/encrypted): <path>`: the PDF can't be opened. Report it to the user.
- `Little or no text …`: OCR was off, unavailable, or found nothing. Report it to the user.
- `Words still run together in places …`: the repair couldn't fix every run. Usually this means poppler couldn't be installed. Say so and suggest `brew install poppler`, then re-run with `-f`. In the meantime, search those files for single distinctive words rather than whole phrases.

The exit status is non-zero if any file failed.

## Reading the output

Each page starts with a `[page N]` line, so you can cite pages and jump around:

```bash
grep -n -i 'sensitivity\|specificity' data/articles/*.txt   # find the passage first
grep -n '^\[page 4\]' "data/articles/Some paper.txt"        # then read around it with Read offset/limit
```

Read only the parts you need, using `grep -n` and Read with `offset`/`limit`, rather than whole files.
