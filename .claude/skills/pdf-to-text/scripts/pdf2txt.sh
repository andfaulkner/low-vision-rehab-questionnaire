#!/usr/bin/env bash
# Convert PDFs to plain-text files, cheaply and incrementally.
#
# Usage: pdf2txt.sh [-o OUTDIR] [-f] [-n] [-r] [-e auto|pdftotext|pdfkit] PATH...
#   PATH     PDF files and/or directories (searched recursively for *.pdf)
#   -o DIR   write .txt files into DIR (default: next to each PDF)
#   -f       force: re-convert even if the .txt is newer than the PDF
#   -n       no OCR: only report PDFs that look scanned, don't OCR them
#   -r       raw: don't repair run-together words
#   -e ENG   extraction engine (default auto: pdftotext, installing poppler if needed;
#            macOS PDFKit if that fails)
#
# Output text has "[page N]" markers, trailing whitespace stripped and blank-line runs
# squeezed. Words the PDF ran together are split again, and a file that still looks
# run together is re-extracted with the other engine. Scanned PDFs are OCR'd with
# macOS Vision. Prints a summary plus only the files that need attention.
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
usage() { sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//'; }
outdir="" force=0 ocr=1 repair=1 engine=auto
while getopts "o:fnre:h" opt; do
  case $opt in
    o) outdir=$OPTARG ;;
    f) force=1 ;;
    n) ocr=0 ;;
    r) repair=0 ;;
    e) engine=$OPTARG ;;
    *) usage; exit 2 ;;
  esac
done
shift $((OPTIND - 1))
[ $# -gt 0 ] || { usage >&2; exit 2; }

have_poppler() {  # pdftotext drops far fewer spaces than PDFKit, so install it if we can
  command -v pdftotext >/dev/null && return 0
  echo "pdf2txt: installing poppler (pdftotext)..." >&2
  if command -v brew >/dev/null; then brew install poppler >/dev/null 2>&1 || true
  elif command -v apt-get >/dev/null && sudo -n true 2>/dev/null; then
    sudo -n apt-get install -y poppler-utils >/dev/null 2>&1 || true
  elif command -v dnf >/dev/null && sudo -n true 2>/dev/null; then
    sudo -n dnf install -y poppler-utils >/dev/null 2>&1 || true
  fi
  command -v pdftotext >/dev/null
}
darwin=0; [ "$(uname)" = Darwin ] && darwin=1
case $engine in
  auto)
    if have_poppler; then engine=pdftotext
    elif [ $darwin = 1 ]; then
      engine=pdfkit; echo "pdf2txt: couldn't install poppler; using PDFKit, which runs more words together" >&2
    else echo "pdf2txt: install poppler-utils (pdftotext)" >&2; exit 1; fi ;;
  pdftotext) have_poppler || { echo "pdf2txt: couldn't install poppler" >&2; exit 1; } ;;
  pdfkit) [ $darwin = 1 ] || { echo "pdf2txt: PDFKit needs macOS" >&2; exit 1; } ;;
  *) usage >&2; exit 2 ;;
esac
# The other engine, for files the first one runs together.
alt=""
if [ "$engine" = pdftotext ] && [ $darwin = 1 ]; then alt=pdfkit
elif [ "$engine" = pdfkit ] && command -v pdftotext >/dev/null; then alt=pdftotext; fi
if [ $repair = 1 ] && ! command -v python3 >/dev/null; then
  echo "pdf2txt: python3 not found; run-together words won't be repaired" >&2; repair=0
fi
[ -n "$outdir" ] && mkdir -p "$outdir"

tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
jobs="$tmp/jobs"; : > "$jobs"   # NUL-separated pairs: pdf, txt
total=0 skipped=0

add() {  # queue one PDF unless its .txt is up to date
  local pdf=$1 txt
  if [ -n "$outdir" ]; then txt="$outdir/$(basename "${pdf%.*}").txt"; else txt="${pdf%.*}.txt"; fi
  total=$((total + 1))
  if [ $force = 0 ] && [ -s "$txt" ] && [ "$txt" -nt "$pdf" ]; then skipped=$((skipped + 1)); return; fi
  printf '%s\0%s\0' "$pdf" "$txt" >> "$jobs"
}

for p in "$@"; do
  if [ -d "$p" ]; then
    while IFS= read -r -d '' f; do add "$f"; done < <(find "$p" -type f -iname '*.pdf' -print0 | sort -z)
  elif [ -f "$p" ]; then add "$p"
  else echo "pdf2txt: not found: $p" >&2; fi
done

clean() {  # raw text (pages split by \f) -> tidy text with [page N] markers
  awk 'BEGIN { RS = "\f"; n = 0 }
       { n++; if (n > 1 && $0 ~ /^[[:space:]]*$/) next   # pdftotext ends with a stray \f
         printf "%s[page %d]\n", (n > 1 ? "\n" : ""), n
         m = split($0, L, "\n"); blank = 1
         for (i = 1; i <= m; i++) { s = L[i]; sub(/[ \t\r]+$/, "", s)
           if (s == "") { if (!blank) print ""; blank = 1 } else { print s; blank = 0 } } }' "$1" > "$2"
}

pdftotext_one() {  # pdf raw -> prints "pages<TAB>chars<TAB>pdf", or ERR
  if pdftotext -enc UTF-8 "$1" "$2" 2>/dev/null; then
    printf '%s\t%s\t%s\n' "$(tr -cd '\f' < "$2" | wc -c | tr -d ' ')" \
      "$(tr -d '[:space:]' < "$2" | wc -c | tr -d ' ')" "$1"
  else
    rm -f "$2"; printf 'ERR\t0\t%s\n' "$1"
  fi
}

ocr_bin=""
get_ocr() {  # compile ocr.swift once into a cache; recompile when the source changes
  [ -n "$ocr_bin" ] && return 0
  [ $darwin = 1 ] && command -v swiftc >/dev/null || return 1
  local bin="${XDG_CACHE_HOME:-$HOME/.cache}/pdf-to-text/ocr"
  if [ ! -x "$bin" ] || [ "$here/ocr.swift" -nt "$bin" ]; then
    mkdir -p "$(dirname "$bin")"
    swiftc -O "$here/ocr.swift" -o "$bin" 2>/dev/null || return 1
  fi
  ocr_bin=$bin
}

# Extract raw text to "<txt>.raw"; record "pages<TAB>chars<TAB>pdf" per file in $stats.
stats="$tmp/stats"; : > "$stats"
if [ -s "$jobs" ]; then
  if [ "$engine" = pdfkit ]; then
    # One osascript process per 200 files; each pdf is followed by its "<txt>.raw" output path.
    xargs -0 -n 400 sh -c 'i=0; for a; do i=$((i+1)); [ $((i%2)) = 0 ] && set -- "$@" "$a.raw" || set -- "$@" "$a"; shift; done; osascript -l JavaScript "$0" "$@"' \
      "$here/pdfkit_extract.js" < "$jobs" 2>/dev/null >> "$stats" || true
    echo >> "$stats"
  else
    while IFS= read -r -d '' pdf && IFS= read -r -d '' txt; do
      pdftotext_one "$pdf" "$txt.raw" >> "$stats"
    done < "$jobs"
  fi
fi

converted=0 failed=0 ocrd=0 sparse="" done_list="$tmp/done"; : > "$done_list"
while IFS= read -r -d '' pdf && IFS= read -r -d '' txt; do
  line="$(grep -F -- "	$pdf" "$stats" | tail -1 || true)"
  pages="${line%%	*}"; rest="${line#*	}"; chars="${rest%%	*}"
  if [ -z "$line" ] || [ "$pages" = ERR ] || [ ! -f "$txt.raw" ]; then
    failed=$((failed + 1)); echo "FAILED (unreadable/encrypted): $pdf"; rm -f "$txt.raw"; continue
  fi
  # Under ~200 non-space chars per page usually means a scanned PDF with no text layer.
  if [ "$pages" -gt 0 ] && [ $((chars / pages)) -lt 200 ]; then
    if [ $ocr = 1 ] && get_ocr && o="$("$ocr_bin" "$pdf" "$txt.ocr" 2>/dev/null)" \
       && [ "${o#*	}" -gt "$chars" ]; then
      mv "$txt.ocr" "$txt.raw"; ocrd=$((ocrd + 1))
    else
      rm -f "$txt.ocr"; sparse="$sparse  $pages pp, $chars chars: $pdf"$'\n'
    fi
  fi
  clean "$txt.raw" "$txt"; rm -f "$txt.raw"
  converted=$((converted + 1))
  printf '%s\0%s\0' "$pdf" "$txt" >> "$done_list"
done < "$jobs"

# Repair run-together words. Words are learned from the converted files plus every
# other .txt already in their folders, so one new PDF still gets a full vocabulary.
fixed=0 retried=0 glued=""
if [ $repair = 1 ] && [ -s "$done_list" ]; then
  txts="$tmp/txts"; lex=()
  tr '\0' '\n' < "$done_list" | awk 'NR % 2 == 0' | tr '\n' '\0' > "$txts"
  while IFS= read -r -d '' d; do lex+=(--lexicon "$d"); done \
    < <(tr '\0' '\n' < "$txts" | sed 's|/[^/]*$||' | sort -u | tr '\n' '\0')
  fix() { python3 -I "$here/fixspaces.py" "${lex[@]}" "$@"; }
  results="$tmp/results"; fix --files-from "$txts" > "$results"

  while IFS= read -r -d '' pdf && IFS= read -r -d '' txt; do
    line="$(grep -F -- "	$txt" "$results" | tail -1 || true)"; [ -n "$line" ] || continue
    IFS=$'\t' read -r fixes left words _ <<< "$line"
    fixed=$((fixed + fixes))
    # Still run together (or needed heavy repair)? Try the other engine and keep the better.
    if [ $((left * 1000)) -ge $((words * 2)) ] || [ $((fixes * 100)) -ge $((words * 3)) ]; then
      if [ -n "$alt" ]; then
        if [ "$alt" = pdfkit ]; then o="$(osascript -l JavaScript "$here/pdfkit_extract.js" "$pdf" "$txt.alt.raw" 2>/dev/null || true)"
        else o="$(pdftotext_one "$pdf" "$txt.alt.raw")"; fi
        if [ -f "$txt.alt.raw" ] && [ "${o%%	*}" != ERR ]; then
          clean "$txt.alt.raw" "$txt.alt"
          IFS=$'\t' read -r f2 l2 _ _ <<< "$(fix "$txt.alt")"
          if [ $((l2 * 20 + f2)) -lt $((left * 20 + fixes)) ]; then
            mv "$txt.alt" "$txt"; left=$l2; retried=$((retried + 1))
          fi
        fi
        rm -f "$txt.alt" "$txt.alt.raw"
      fi
      [ "$left" -ge 5 ] && glued="$glued  $left long runs: $txt"$'\n'
    fi
  done < "$done_list"
fi

echo "pdf2txt [$engine]: $total PDFs, $converted converted ($ocrd via OCR), $skipped up to date, $failed failed;" \
  "$fixed run-together words split$([ $retried -gt 0 ] && echo ", $retried files re-extracted with $alt")"
if [ -n "$sparse" ]; then
  echo "Little or no text (scanned or image-only; check these by hand):"; printf '%s' "$sparse"
fi
if [ -n "$glued" ]; then
  echo "Words still run together in places (grep may miss phrases there):"; printf '%s' "$glued"
fi
[ $failed = 0 ]
