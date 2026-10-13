"""Re-insert spaces that PDF text extraction dropped ("Weanalyzeddatafrom385adults").

Usage: python3 -I fixspaces.py [--lexicon FILE ...] TXT...
Edits each TXT in place and prints "fixes<TAB>words<TAB>path" per file.

Word frequencies come from the text files themselves (plus any --lexicon files and
the system word list), so domain terms like "logMAR" or "VA" are known words.
A run of letters is only split when every piece is a known word and the split is
far more likely than the run being one word, so normal text is left alone.
"""
import math
import re
import sys
from collections import Counter
from pathlib import Path

# Short words allowed as pieces of a split. Other 1-3 letter pieces are rejected, which
# stops names and foreign words being chopped into fragments ("Barbazetto" -> "Barb az et to").
COMMON = set("""a act add age aid aim all an and any are as ask at bad be big but by can car
day did do due end eye far few for get go had has he her him his how i if in is it its key
low man may me men my net new no nor not now of off old on one or our out own per put red
run say see set sex she six so sum ten the too top try two up us use via was way we who why
yes yet you""".split())

LETTERS = r"[^\W\d_]+"   # unicode letters, so "Rodríguez" stays one word
WORD = re.compile(LETTERS)
# Whitespace-separated tokens to leave alone: URLs, emails, DOIs, dot leaders.
SKIP = re.compile(r"://|www\.|@|doi|\.\.\.|^[\W\d_]*$", re.I)


def load_system_words():
    for path in ("/usr/share/dict/words", "/usr/share/dict/web2"):
        try:
            return {w.lower() for w in Path(path).read_text(errors="ignore").split() if len(w) >= 4}
        except OSError:
            pass
    return set()


class Splitter:
    def __init__(self, texts):
        words = [w for t in texts for w in WORD.findall(t)]
        self.exact = Counter(words)
        self.counts = Counter(w.lower() for w in words)
        self.total = sum(self.counts.values()) or 1
        self.system = load_system_words()
        self.maxlen = 30
        self.cache = {}

    def known(self, w):
        return w in self.system or w in COMMON or self.counts[w] >= 2

    def cost(self, piece):
        """-log(probability) of a piece (original case), or None if it can't be a piece."""
        w = piece.lower()
        if len(w) <= 3:
            # Short pieces: common words, or acronyms seen standalone often ("VA", "PRL").
            ok = (w in COMMON and (len(w) > 1 or w == "a")) or \
                 (len(w) > 1 and piece.isupper() and self.exact[piece] >= 3)
        else:
            ok = w in self.system or self.counts[w] >= 2
        if not ok:
            return None
        return math.log(self.total / max(self.counts[w], 0.5)) + 1.0   # +1 per piece favours fewer pieces

    def split(self, run):
        """Best segmentation of a letter run, or None to leave it as is."""
        if run in self.cache:
            return self.cache[run]
        n = len(run)
        best = [(0.0, 0)] + [(math.inf, 0)] * n
        for end in range(1, n + 1):
            for start in range(max(0, end - self.maxlen), end):
                c = self.cost(run[start:end])
                if c is not None and best[start][0] + c < best[end][0]:
                    best[end] = (best[start][0] + c, start)
        result = None
        if best[n][0] < math.inf:
            pieces, end = [], n
            while end > 0:
                start = best[end][1]
                pieces.append(run[start:end])
                end = start
            pieces.reverse()
            key = run.lower()
            whole = math.log(self.total / self.counts[key]) + 1.0 if self.known(key) and self.counts[key] else None
            plausible = (
                len(pieces) > 1
                and pieces[-1].lower() != "a"   # names often end in "a": "Suzana" is not "Suzan a"
                # Unless every piece is a common word ("ofthe"), pieces must be long on average,
                # so foreign words aren't split into short English ones ("Tornando" -> "Torn an do").
                and (all(p.lower() in COMMON for p in pieces) or n / len(pieces) >= 4)
            )
            if plausible and (whole is None if self.known(key) is False else whole is not None and best[n][0] < whole):
                result = pieces
        self.cache[run] = result
        return result

    def fix_token(self, tok):
        """Return (fixed token, number of words split out)."""
        if SKIP.search(tok):
            return tok, 0
        parts, fixes = [], 0
        for m in re.finditer(LETTERS + r"|\d+(?:\.\d+)*|[\W_]+", tok):
            s = m.group()
            pieces = self.split(s) if s[0].isalpha() and len(s) >= 5 else None
            if pieces:
                fixes += len(pieces) - 1
                parts.append(" ".join(pieces))
            else:
                parts.append(s)
        if not fixes:
            return tok, 0
        # The token really was glued, so also space out letter/number and ".,;:" joins.
        out = parts[0]
        for prev, cur in zip(parts, parts[1:]):
            a, b = prev[-1], cur[0]
            if (a.isalpha() and len(prev) > 2 and cur[0].isdigit()) or \
               (a.isdigit() and b.isalpha() and len(cur) > 2) or \
               (a in ".,;:" and len(prev) == 1 and b.isalpha() and out[-2:].isalpha()):
                out += " "
            out += cur
        return out, fixes


def main(argv):
    lex, files, dry = [], [], False
    i = 0
    while i < len(argv):
        if argv[i] == "--lexicon":
            lex.append(argv[i + 1])
            i += 1
        elif argv[i] == "--dry-run":   # print each change instead of editing files
            dry = True
        else:
            files.append(argv[i])
        i += 1
    texts = {f: Path(f).read_text(errors="ignore") for f in files}
    extra = [Path(f).read_text(errors="ignore") for f in lex if f not in texts]
    sp = Splitter(list(texts.values()) + extra)
    for f, text in texts.items():
        fixes = 0

        def repl(m):
            nonlocal fixes
            new, n = sp.fix_token(m.group())
            if n and dry:
                print(f"  {m.group()}  ->  {new}")
            fixes += n
            return new

        fixed = re.sub(r"\S{5,}", repl, text)
        if fixes and not dry:
            Path(f).write_text(fixed)
        print(f"{fixes}\t{len(text.split())}\t{f}")


if __name__ == "__main__":
    main(sys.argv[1:])
