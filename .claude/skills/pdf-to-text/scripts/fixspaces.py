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

COMMON = """a about after all also an and any are as at be been between both but by can
could did do does each either for from had has have he her his how i if in into is it
its may more most no not of on one only or other our out over per she so some such than
that the their them then there these they this those through to two under up use used
using was we were what when where which while who whom why will with within without
would you your""".split()

WORD = re.compile(r"[A-Za-z]+")
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
        self.counts = Counter(w.lower() for t in texts for w in WORD.findall(t))
        self.total = sum(self.counts.values()) or 1
        self.system = load_system_words()
        self.common = set(COMMON)
        self.maxlen = 30
        self.cache = {}

    def known(self, w):
        return w in self.system or w in self.common or self.counts[w] >= 3

    def cost(self, w):
        """-log(probability) of w as a piece, or None if w can't be a piece."""
        n = self.counts[w]
        if len(w) == 1 and w not in ("a", "i"):
            return None
        if len(w) <= 3 and w not in self.common and n < 3:
            return None   # keep junk like "ae", "nds" out of splits
        if n < 2 and w not in self.common and w not in self.system:
            return None
        return math.log(self.total / max(n, 0.5)) + 1.0   # +1 per piece favours fewer pieces

    def split(self, run):
        """Best segmentation of a letter run, or None to leave it as is."""
        key = run.lower()
        if key in self.cache:
            return self.cache[key]
        n = len(key)
        best = [(0.0, 0)] + [(math.inf, 0)] * n
        for end in range(1, n + 1):
            for start in range(max(0, end - self.maxlen), end):
                c = self.cost(key[start:end])
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
            whole = self.cost(key) if self.known(key) else None
            if len(pieces) > 1 and (whole is None or best[n][0] < whole):
                result = pieces
        self.cache[key] = result
        return result

    def fix_token(self, tok):
        """Return (fixed token, number of words split out)."""
        if SKIP.search(tok):
            return tok, 0
        parts, fixes = [], 0
        for m in re.finditer(r"[A-Za-z]+|\d+(?:\.\d+)*|[^A-Za-z\d]+", tok):
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
            if (a.isalpha() and len(prev) > 2 and cur.isdigit()) or \
               (a.isdigit() and b.isalpha() and len(cur) > 2) or \
               (a in ".,;:" and b.isalpha() and prev[:-1][-2:].isalpha()):
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
