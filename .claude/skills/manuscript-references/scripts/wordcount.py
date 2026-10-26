"""Count body words of paper/manuscript.md per section.

Body = everything from the first paragraph after the byline to the end of the
CONCLUSION section, excluding: the DRAFT note, title, dek, byline, boxes
(<!-- box:start --> ... <!-- box:end -->), figure captions, tables, the
reference list, the author block and the supplement list. Citation keys
[@...] and [VERIFY ...] tags are stripped before counting.
"""
import re
import sys

path = sys.argv[1]
lines = open(path, encoding="utf-8").read().split("\n")

in_box = False
started = False
sections = []
current = None
body_words = 0


def clean(s):
    s = re.sub(r"\[@[^\]]*\]", "", s)
    s = re.sub(r"\[(VERIFY|UPDATE|PENDING)[^\]]*\]", "", s)
    s = s.replace("**", "")
    return s


for ln in lines:
    if "<!-- box:start -->" in ln:
        in_box = True
        continue
    if "<!-- box:end -->" in ln:
        in_box = False
        continue
    if in_box:
        continue
    if ln.startswith("BY "):
        started = True
        continue
    if not started:
        continue
    if ln.startswith("## "):
        head = ln[3:].strip()
        if head == "References":
            break
        current = [head, 0]
        sections.append(current)
        continue
    if ln.startswith("---"):
        if current and current[0] == "CONCLUSION":
            break
        continue
    if ln.startswith("**Figure") or ln.startswith("**Table") or ln.startswith("|"):
        continue
    text = clean(ln).strip()
    if not text:
        continue
    n = len(text.split())
    body_words += n
    if current is None:
        current = ["(introduction)", 0]
        sections.append(current)
    current[1] += n

for name, n in sections:
    print(f"{n:6d}  {name}")
print(f"{body_words:6d}  TOTAL body words")
print(f"{len([s for s in sections if s[0] != '(introduction)']):6d}  headings")
