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
day did do due end et eye far few for get go had has he her him his how i if in is it its key
low man may me men my net new no nor not now of off old on one or our out own per put red
run say see set sex she six so sum ten the to too top try two up us use via vs was way we who
why yes yet you""".split())

# Combining forms that start closed compounds ("autorefraction", "neuroophthalmology").
PREFIXES = set("""anti auto bio electro hemi hyper hypo inter intra macro micro mini mono multi
neuro oculo opto para peri photo poly pseudo psycho quasi retro semi socio super tele ultra
uni visuo""".split())

LETTERS = r"[^\W\d_]+"   # unicode letters, so "Rodríguez" stays one word
WORD = re.compile(LETTERS)
# Whitespace-separated tokens to leave alone: URLs, paths, emails, DOIs, dot leaders.
SKIP = re.compile(r"://|www\.|@|/|doi|\.\.\.|^[\W\d_]*$|\b10\.\d{4}"
                  r"|\w\.(com|org|net|edu|gov|int|io|ca|uk|au|br|de|fr|es|it|nl)\b", re.I)
# Missing space after punctuation between words: "Prospective,observational",
# "services.From". Not "e.g.", "index.html", "U.S.A" or "1,000".
PUNCT = re.compile(r"(?<=[^\W\d_]{3})[,;:](?=[^\W\d_]{3})|(?<=[a-z]{3})\.(?=[A-Z][a-z]{2})")
SUFFIXES = [("ies", "y"), ("es", ""), ("s", ""), ("ed", ""), ("ed", "e"), ("ing", ""), ("ing", "e"),
            ("ly", ""), ("ers", ""), ("er", ""), ("ness", ""), ("able", ""), ("able", "e"),
            ("ations", "e"), ("ation", "e"), ("al", "")]


def load_system_words():
    for path in ("/usr/share/dict/words", "/usr/share/dict/web2"):
        try:
            return {w.lower() for w in Path(path).read_text(errors="ignore").split() if len(w) >= 4}
        except OSError:
            pass
    return set()


class Splitter:
    def __init__(self, texts):
        # Skip words straight after a hyphen: they're often fragments ("organiza-tions").
        words = [w for t in texts for w in re.findall(r"(?<![-\u00ad\w])" + LETTERS, t)]
        self.exact = Counter(words)
        self.counts = Counter(w.lower() for w in words)
        self.total = sum(self.counts.values()) or 1
        # Adjacent word pairs, across spaces, newlines and hyphens ("injury-related").
        self.pairs = Counter()
        for t in texts:
            toks = re.findall(LETTERS + r"|[^\s\w-]", t.lower())
            self.pairs.update(zip(toks, toks[1:]))
        self.system = load_system_words()
        self.maxlen = 30
        self.cache = {}

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

    def segment(self, run):
        """Cheapest split of a run into 2+ valid pieces: (cost, pieces) or (inf, None)."""
        n = len(run)
        best = [(0.0, 0)] + [(math.inf, 0)] * n
        for end in range(1, n + 1):
            for start in range(max(0, end - self.maxlen, 1 if end == n else 0), end):
                c = self.cost(run[start:end])
                if c is not None and best[start][0] + c < best[end][0]:
                    best[end] = (best[start][0] + c, start)
        if best[n][0] == math.inf:
            return math.inf, None
        pieces, end = [], n
        while end > 0:
            start = best[end][1]
            pieces.append(run[start:end])
            end = start
        return best[n][0], pieces[::-1]

    def in_dictionary(self, w):
        """w or a simple inflection of it is in the system word list ("inaccuracies")."""
        us = re.sub(r"(?<=\w{3})is(?=[aei])", "iz", w)   # British "-ise" spellings ("generalisable")
        return any(v in self.system or any(
            v.endswith(suf) and v[: -len(suf)] + add in self.system
            for suf, add in SUFFIXES if len(v) - len(suf) >= 4) for v in {w, us})

    def plausible(self, run, pieces):
        """Is there real evidence that this run is several words glued together?"""
        low = [p.lower() for p in pieces]
        if len(pieces) < 2 or low[-1] == "a":   # names often end in "a": "Suzana" is not "Suzan a"
            return False
        if len(pieces) == 2 and low[0] in PREFIXES:
            return False
        # Pairs with a short common word ("program as") need more evidence than other pairs.
        pairs_seen = any(self.pairs[(x, y)] >= (3 if min(len(x), len(y)) <= 3 else 1)
                         for x, y in zip(low, low[1:]))
        common = sum(p in COMMON for p in low)
        if common == len(pieces):            # "ofthe", "andthe"; not names like "Anand", "Arean"
            return run.islower()
        if len(run) / len(pieces) < 4:       # stops "Tornando" -> "Torn an do"
            return False
        # Lowercase then capital ("visionControl", "aHealthier"), or a surname glued to its
        # initials ("MassofRW"). Title+Title ("VectorVision") is often a brand name, so it
        # falls through to the side-by-side evidence below ("Mann Whitney").
        if len(pieces) <= 3 and (pieces[0][0].islower() and not pieces[-1].islower()
                                 or pieces[-1].isupper() and len(pieces[-1]) <= 3 and pieces[0][0].isupper()):
            return True
        if len(pieces) >= 3:                 # PDFKit-style runs: "Weanalyzeddatafrom"
            return pairs_seen or 2 * common >= len(pieces)
        # Two words: only if they also appear side by side elsewhere ("pilot trial",
        # "injury-related"). Keeps surnames ("Rosenstein") and compounds ("Bluetooth") intact.
        return pairs_seen

    def split(self, run):
        """Pieces to replace a letter run with, or None to leave it as is."""
        if run not in self.cache:
            self.cache[run] = None   # guards the recursion below
            cost, pieces = self.segment(run)
            result = None
            if pieces:
                # Pieces can be glue that recurs elsewhere ("and" + "visualinformationprocessing").
                pieces = [q for p in pieces for q in (self.split(p) if len(p) >= 5 else None) or [p]]
            if pieces and self.plausible(run, pieces):
                # A real word ("baseline", "lifespan") stays unless the split is far likelier;
                # repeated glue ("ofthe" x 30) still loses to its common pieces. Glue of 3+
                # words that recurs a few times (page headers) doesn't count as a word.
                n = self.counts[run.lower()]
                whole = math.log(self.total / max(n, 0.5)) + 1.0 \
                    if self.in_dictionary(run.lower()) or n >= 5 or (n >= 2 and len(pieces) == 2) \
                    else math.inf
                if cost < whole:
                    result = pieces
            self.cache[run] = result
        return self.cache[run]

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
        out = parts[0]
        if fixes:   # the token really was glued, so also space out letter/number joins
            for prev, cur in zip(parts, parts[1:]):
                if (prev[-1].isalpha() and len(prev) > 2 and cur[0].isdigit()) or \
                   (prev[-1].isdigit() and cur[0].isalpha() and len(cur) > 2):
                    out += " "
                out += cur
        else:
            out = tok
        out, n = PUNCT.subn(lambda m: m.group() + " ", out)
        return out, fixes + n


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
