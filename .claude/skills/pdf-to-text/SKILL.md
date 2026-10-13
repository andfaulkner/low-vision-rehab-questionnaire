---
name: pdf-to-text
description: Cheaply convert PDFs (e.g. the articles in data/articles/) into plain .txt files with a script, so they can be grepped and read in parts instead of loading whole PDFs into context. Use when asked to convert, extract text from, OCR, or read/search the full text of one or more PDFs.
---

# PDF to text

Do everything with the script. Don't open PDFs with the Read tool to extract text, because that is far more expensive than reading the `.txt`.

```bash
.claude/skills/pdf-to-text/scripts/pdf2txt.sh [-o OUTDIR] [-f] [-n] [-e auto|pdftotext|pdfkit] PATH...
```

- `PATH` is any mix of PDF files and directories (searched recursively).
- By default each `foo.pdf` gets a `foo.txt` next to it. Use `-o DIR` to write the text files somewhere else instead (e.g. the scratchpad for one-off reads).
- It's incremental: a PDF whose `.txt` is already newer than it is skipped, so re-running it on a whole folder is cheap. Use `-f` to force re-conversion.
- The engine is `pdftotext` (poppler) if installed, and macOS's built-in PDFKit if not. `pdftotext` drops far fewer spaces between words, so prefer it (`brew install poppler`).
- PDFs with almost no text layer (scanned) are OCR'd automatically with macOS Vision. This takes about 1s per page, and the first use compiles a helper into `~/.cache/pdf-to-text/`. Use `-n` to skip OCR and just list them.

The script prints a single summary line. It prints extra lines only for files that need attention, so its output stays small:

- `FAILED (unreadable/encrypted): <path>`: the PDF can't be opened. Report it to the user.
- `Little or no text …`: OCR was off, unavailable, or found nothing. Report it to the user.

The exit status is non-zero if any file failed.

## Reading the output

Each page starts with a `[page N]` line, so you can cite pages and jump around:

```bash
grep -n -i 'sensitivity\|specificity' data/articles/*.txt   # find the passage first
grep -n '^\[page 4\]' "data/articles/Some paper.txt"        # then read around it with Read offset/limit
```

Read only the parts you need, using `grep -n` and Read with `offset`/`limit`, rather than whole files.
