#!/usr/bin/env bash
# Convert PDFs to plain-text files, cheaply and incrementally.
#
# Usage: pdf2txt.sh [-o OUTDIR] [-f] [-n] [-e auto|pdftotext|pdfkit] PATH...
#   PATH     PDF files and/or directories (searched recursively for *.pdf)
#   -o DIR   write .txt files into DIR (default: next to each PDF)
#   -f       force: re-convert even if the .txt is newer than the PDF
#   -n       no OCR: only report PDFs that look scanned, don't OCR them
#   -e ENG   extraction engine (default auto: pdftotext if installed, else macOS PDFKit)
#
# Output text has "[page N]" markers, trailing whitespace stripped and blank-line
# runs squeezed. PDFs with almost no text layer are OCR'd with macOS Vision.
# Prints only a summary plus files that need attention, however many PDFs there are.
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
usage() { sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'; }
outdir="" force=0 ocr=1 engine=auto
while getopts "o:fne:h" opt; do
  case $opt in
    o) outdir=$OPTARG ;;
    f) force=1 ;;
    n) ocr=0 ;;
    e) engine=$OPTARG ;;
    *) usage; exit 2 ;;
  esac
done
shift $((OPTIND - 1))
[ $# -gt 0 ] || { usage >&2; exit 2; }

if [ "$engine" = auto ]; then
  if command -v pdftotext >/dev/null; then engine=pdftotext
  elif [ "$(uname)" = Darwin ]; then engine=pdfkit
  else echo "pdf2txt: install poppler (pdftotext)" >&2; exit 1; fi
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

ocr_bin=""
get_ocr() {  # compile ocr.swift once into a cache; recompile when the source changes
  [ -n "$ocr_bin" ] && return 0
  [ "$(uname)" = Darwin ] && command -v swiftc >/dev/null || return 1
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
      if pdftotext -enc UTF-8 "$pdf" "$txt.raw" 2>/dev/null; then
        printf '%s\t%s\t%s\n' "$(tr -cd '\f' < "$txt.raw" | wc -c | tr -d ' ')" \
          "$(tr -d '[:space:]' < "$txt.raw" | wc -c | tr -d ' ')" "$pdf" >> "$stats"
      else
        printf 'ERR\t0\t%s\n' "$pdf" >> "$stats"; rm -f "$txt.raw"
      fi
    done < "$jobs"
  fi
fi

converted=0 failed=0 ocrd=0 sparse=""
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
done < "$jobs"

echo "pdf2txt [$engine]: $total PDFs, $converted converted ($ocrd via OCR), $skipped up to date, $failed failed"
if [ -n "$sparse" ]; then
  echo "Little or no text (scanned or image-only; check these by hand):"; printf '%s' "$sparse"
fi
[ $failed = 0 ]
