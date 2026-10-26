"""Shared helpers for the screening-workbook skill (standard library only).

Reads an .xlsx as a zip of XML parts, reads cells from the sheet XML and
sharedStrings, edits cells by rewriting the sheet XML text in place (so the
x14 drop-down validations, conditional formatting, hyperlinks and styles that
openpyxl would drop are untouched), re-evaluates the Counts formulas and
patches their cached <v> values, and writes the zip back with every other part
copied byte for byte.

Only the few formula shapes used on the Counts tab are evaluated (+, -, *,
=, <>, cell refs, COUNTA, COUNTIF, SUMPRODUCT). Anything else raises
FormulaError so that stale cached values are never silently left behind.
"""

import csv
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter, namedtuple

NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_PKG = "http://schemas.openxmlformats.org/package/2006/relationships"

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.abspath(os.path.join(SKILL_DIR, "..", "..", ".."))
DEFAULT_XLSX = os.path.join(REPO_ROOT, "data", "LVR_screening_sheet_2.xlsx")
DEFAULT_DATA_DIR = os.path.join(REPO_ROOT, "data")
DEFAULT_TEXT_DIR = os.path.join(REPO_ROOT, "data", "articles_text")

SCREENING = "Screening"
COUNTS = "Counts"
LISTS = "Lists"

# Screening columns. H-L belong to the human reviewer; N-S are AI columns.
REVIEWER_COLS = ("H", "I", "J", "K", "L")
AI_COLS = ("N", "O", "P", "Q", "R", "S")
NUMERIC_COLS = ("A", "B")

# Which Lists column validates which Screening column (mirrors the x14 rules
# for H, I, J, K; N-S are checked against the same lists for consistency).
LIST_FOR_COL = {
    "H": "A", "N": "A", "Q": "A",          # Include / Exclude / Maybe
    "J": "B",                              # Include / Exclude
    "I": "C", "K": "C", "O": "C", "R": "C",  # the 10 exclusion reasons
}

Cell = namedtuple("Cell", "ref value kind style formula")
# kind: 'n' number, 's' shared string, 'inlineStr', 'str' (formula string),
#       'b' boolean, 'e' error, 'blank'


class WorkbookError(Exception):
    pass


class FormulaError(WorkbookError):
    pass


# ----------------------------------------------------------------- refs ----

def col_to_idx(col):
    n = 0
    for ch in col:
        n = n * 26 + (ord(ch) - 64)
    return n


def idx_to_col(i):
    s = ""
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


def split_ref(ref):
    m = re.fullmatch(r"\$?([A-Z]{1,3})\$?(\d+)", ref)
    if not m:
        raise WorkbookError("bad cell reference %r" % ref)
    return m.group(1), int(m.group(2))


def xml_escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def xml_attr_escape(s):
    return xml_escape(s).replace('"', "&quot;")


def _text_of(elem):
    """Concatenate every <t> under a <si> or <is> (handles rich-text runs)."""
    return "".join(t.text or "" for t in elem.iter("{%s}t" % NS_MAIN))


def fmt_number(x):
    if isinstance(x, bool):
        return "1" if x else "0"
    if isinstance(x, int) or (isinstance(x, float) and x.is_integer()):
        return str(int(x))
    return repr(float(x))


# ------------------------------------------------------------- workbook ----

class Workbook:
    def __init__(self, path):
        self.path = path
        with zipfile.ZipFile(path) as zf:
            self.infos = zf.infolist()
            self.parts = {i.filename: zf.read(i.filename) for i in self.infos}
        self.sheet_files = self._map_sheets()
        self.sst = self._load_sst()
        self._cells_cache = {}
        self._memo = {}

    # -- package structure
    def _map_sheets(self):
        wb = ET.fromstring(self.parts["xl/workbook.xml"])
        rels = ET.fromstring(self.parts["xl/_rels/workbook.xml.rels"])
        targets = {r.get("Id"): r.get("Target") for r in rels.iter("{%s}Relationship" % NS_PKG)}
        out = {}
        for sh in wb.iter("{%s}sheet" % NS_MAIN):
            target = targets[sh.get("{%s}id" % NS_R)]
            out[sh.get("name")] = "xl/" + target.lstrip("/").removeprefix("xl/")
        return out

    def _load_sst(self):
        if "xl/sharedStrings.xml" not in self.parts:
            return []
        root = ET.fromstring(self.parts["xl/sharedStrings.xml"])
        return [_text_of(si) for si in root.iter("{%s}si" % NS_MAIN)]

    def sheet_part(self, name):
        try:
            return self.sheet_files[name]
        except KeyError:
            raise WorkbookError("no sheet named %r (have %s)" % (name, ", ".join(self.sheet_files)))

    def text(self, part):
        return self.parts[part].decode("utf-8")

    def set_text(self, part, s):
        self.parts[part] = s.encode("utf-8")
        self._cells_cache.clear()

    # -- reading
    def cells(self, name):
        """dict ref -> Cell for one sheet, using cached values for formulas."""
        if name in self._cells_cache:
            return self._cells_cache[name]
        root = ET.fromstring(self.parts[self.sheet_part(name)])
        out = {}
        for c in root.iter("{%s}c" % NS_MAIN):
            ref = c.get("r")
            t = c.get("t")
            s = c.get("s")
            f = c.find("{%s}f" % NS_MAIN)
            formula = f.text if f is not None else None
            v = c.find("{%s}v" % NS_MAIN)
            if t == "s":
                val, kind = self.sst[int(v.text)], "s"
            elif t == "inlineStr":
                val, kind = _text_of(c.find("{%s}is" % NS_MAIN)), "inlineStr"
            elif t == "str":
                val, kind = (v.text or "") if v is not None else "", "str"
            elif t == "b":
                val, kind = ("TRUE" if v is not None and v.text == "1" else "FALSE"), "b"
            elif t == "e":
                val, kind = (v.text if v is not None else "#N/A"), "e"
            elif v is not None and v.text is not None:
                val, kind = v.text, "n"
            else:
                val, kind = None, "blank"
            out[ref] = Cell(ref, val, kind, s, formula)
        self._cells_cache[name] = out
        return out

    def value(self, name, ref):
        c = self.cells(name).get(ref)
        return None if c is None else c.value

    def hyperlinks(self, name):
        """dict ref -> external URL for one sheet."""
        part = self.sheet_part(name)
        root = ET.fromstring(self.parts[part])
        relpart = part.replace("worksheets/", "worksheets/_rels/") + ".rels"
        targets = {}
        if relpart in self.parts:
            rels = ET.fromstring(self.parts[relpart])
            targets = {r.get("Id"): r.get("Target") for r in rels.iter("{%s}Relationship" % NS_PKG)}
        out = {}
        for h in root.iter("{%s}hyperlink" % NS_MAIN):
            rid = h.get("{%s}id" % NS_R)
            if rid and rid in targets:
                out[h.get("ref")] = targets[rid]
            elif h.get("location"):
                out[h.get("ref")] = h.get("location")
        return out

    def extent(self, name):
        """(max_row, max_col_index) from the cells actually present."""
        mr = mc = 0
        for ref in self.cells(name):
            col, row = split_ref(ref)
            mr = max(mr, row)
            mc = max(mc, col_to_idx(col))
        return mr, mc

    def grid(self, name, links_as_urls=True):
        """Rows 1..max_row x cols 1..max_col as strings ('' for blanks).
        A cell that carries a hyperlink is replaced by its URL, which is how
        the DOI column is exported."""
        cells = self.cells(name)
        links = self.hyperlinks(name) if links_as_urls else {}
        mr, mc = self.extent(name)
        rows = []
        for r in range(1, mr + 1):
            row = []
            for ci in range(1, mc + 1):
                ref = "%s%d" % (idx_to_col(ci), r)
                if ref in links:
                    row.append(links[ref])
                else:
                    c = cells.get(ref)
                    row.append("" if c is None or c.value is None else c.value)
            rows.append(row)
        return rows

    def dimension_last_row(self, name):
        m = re.search(r'<dimension ref="[A-Z]+\d+:[A-Z]+(\d+)"', self.text(self.sheet_part(name)))
        return int(m.group(1)) if m else self.extent(name)[0]

    def header_map(self, name=SCREENING):
        """column letter -> header text (row 1)."""
        out = {}
        for ref, c in self.cells(name).items():
            col, row = split_ref(ref)
            if row == 1 and c.value:
                out[col] = c.value
        return out

    def lists(self):
        """Allowed drop-down values from the Lists tab: {'A': [...], 'B': [...], 'C': [...]}."""
        out = {}
        for ref, c in self.cells(LISTS).items():
            col, row = split_ref(ref)
            if row >= 2 and c.value not in (None, ""):
                out.setdefault(col, []).append((row, c.value))
        return {k: [v for _, v in sorted(vs)] for k, vs in out.items()}

    def id_to_row(self, name=SCREENING):
        out = {}
        for ref, c in self.cells(name).items():
            col, row = split_ref(ref)
            if col == "A" and row >= 2 and c.value not in (None, ""):
                try:
                    out[int(float(c.value))] = row
                except ValueError:
                    pass
        return out

    def default_styles(self, name=SCREENING):
        """Most common style index per column in data rows (row >= 2).
        Memoised: styles do not change through set_cell."""
        key = ("styles", name)
        if key not in self._memo:
            cnt = {}
            for ref, c in self.cells(name).items():
                col, row = split_ref(ref)
                if row >= 2 and c.style is not None:
                    cnt.setdefault(col, Counter())[c.style] += 1
            self._memo[key] = {col: ctr.most_common(1)[0][0] for col, ctr in cnt.items()}
        return self._memo[key]

    def column_is_numeric(self, name, col):
        key = ("numeric", name, col)
        if key not in self._memo:
            kinds = Counter(c.kind for ref, c in self.cells(name).items()
                            if split_ref(ref)[0] == col and split_ref(ref)[1] >= 2 and c.kind != "blank")
            self._memo[key] = bool(kinds) and kinds.most_common(1)[0][0] == "n"
        return self._memo[key]

    # -- writing
    def set_cell(self, name, ref, value, as_number=None):
        """Set one cell by rewriting the sheet XML. value None/'' clears it.
        Strings are written as inline strings (no sharedStrings edit needed);
        numbers as plain <v>. Styles are kept, or copied from the column."""
        part = self.sheet_part(name)
        xml = self.text(part)
        col, row = split_ref(ref)
        ref = "%s%d" % (col, row)
        if as_number is None:
            as_number = (value not in (None, "")
                         and re.fullmatch(r"-?\d+(\.\d+)?", str(value)) is not None
                         and self.column_is_numeric(name, col))
        defaults = self.default_styles(name)

        row_m = re.search(r'<row r="%d"(?P<attrs>[^>]*?)(?P<selfclose>/)?>' % row, xml)
        if row_m is None:
            xml = self._insert_row(xml, name, row, defaults)
            row_m = re.search(r'<row r="%d"(?P<attrs>[^>]*?)(?P<selfclose>/)?>' % row, xml)
        if row_m.group("selfclose"):
            xml = xml[:row_m.end() - 2] + "></row>" + xml[row_m.end():]
            row_m = re.search(r'<row r="%d"(?P<attrs>[^>]*?)>' % row, xml)
        row_end = xml.index("</row>", row_m.end())
        row_body = xml[row_m.end():row_end]

        cell_re = re.compile(r'<c r="%s"(?: s="(?P<s>\d+)")?(?: t="[^"]*")?(?:/>|>.*?</c>)' % ref, re.S)
        cm = cell_re.search(row_body)
        style = cm.group("s") if cm and cm.group("s") else defaults.get(col)
        s_attr = ' s="%s"' % style if style is not None else ""
        if value is None or value == "":
            new = '<c r="%s"%s/>' % (ref, s_attr)
        elif as_number:
            new = '<c r="%s"%s><v>%s</v></c>' % (ref, s_attr, value)
        else:
            text = str(value)
            space = ' xml:space="preserve"' if text != text.strip() or "\n" in text else ""
            new = '<c r="%s"%s t="inlineStr"><is><t%s>%s</t></is></c>' % (ref, s_attr, space, xml_escape(text))

        if cm:
            row_body = row_body[:cm.start()] + new + row_body[cm.end():]
        else:
            # insert in column order
            pos = len(row_body)
            for m in re.finditer(r'<c r="([A-Z]+)\d+"', row_body):
                if col_to_idx(m.group(1)) > col_to_idx(col):
                    pos = m.start()
                    break
            row_body = row_body[:pos] + new + row_body[pos:]
        xml = xml[:row_m.end()] + row_body + xml[row_end:]
        xml = self._bump_dimension(xml, col, row)
        self.set_text(part, xml)

    def _insert_row(self, xml, name, row, defaults):
        prev = None
        for m in re.finditer(r'<row r="(\d+)"([^>]*?)/?>', xml):
            r = int(m.group(1))
            if r < row:
                prev = m
            elif r > row:
                break
        attrs = ""
        if prev is not None:
            attrs = re.sub(r' spans="[^"]*"', "", prev.group(2))
        cells = "".join('<c r="%s%d" s="%s"/>' % (c, row, s)
                        for c, s in sorted(defaults.items(), key=lambda kv: col_to_idx(kv[0])))
        new_row = '<row r="%d"%s>%s</row>' % (row, attrs, cells)
        if prev is not None:
            end = xml.index("</row>", prev.end()) + len("</row>") if not prev.group(0).endswith("/>") else prev.end()
            return xml[:end] + new_row + xml[end:]
        i = xml.index("</sheetData>")
        return xml[:i] + new_row + xml[i:]

    def _bump_dimension(self, xml, col, row):
        m = re.search(r'<dimension ref="([A-Z]+)(\d+):([A-Z]+)(\d+)"', xml)
        if not m:
            return xml
        c1, r1, c2, r2 = m.group(1), int(m.group(2)), m.group(3), int(m.group(4))
        c2 = col if col_to_idx(col) > col_to_idx(c2) else c2
        r2 = max(r2, row)
        return xml[:m.start()] + '<dimension ref="%s%d:%s%d"' % (c1, r1, c2, r2) + xml[m.end():]

    def extend_ranges(self, new_last_row):
        """Grow every range that ends at the Screening sheet's current last row
        (dimension, autoFilter, conditional formatting, x14 validations, the
        _FilterDatabase name and the Counts formulas) to new_last_row."""
        old = self.dimension_last_row(SCREENING)
        if new_last_row <= old:
            return old
        bump = re.compile(r"(:\$?[A-Z]{1,3}\$?)%d(?!\d)" % old)
        repl = r"\g<1>%d" % new_last_row

        def in_attr(xml, tag, attr):
            return re.sub(r'(<%s [^>]*?%s=")([^"]*)(")' % (tag, attr),
                          lambda m: m.group(1) + bump.sub(repl, m.group(2)) + m.group(3), xml)

        def in_elem(xml, tag):
            return re.sub(r"(<%s(?: [^>]*)?>)(.*?)(</%s>)" % (tag, tag),
                          lambda m: m.group(1) + bump.sub(repl, m.group(2)) + m.group(3), xml, flags=re.S)

        part = self.sheet_part(SCREENING)
        xml = self.text(part)
        xml = in_attr(xml, "dimension", "ref")
        xml = in_attr(xml, "autoFilter", "ref")
        xml = in_attr(xml, "conditionalFormatting", "sqref")
        xml = in_elem(xml, "xm:sqref")
        self.set_text(part, xml)
        self.set_text("xl/workbook.xml", in_elem(self.text("xl/workbook.xml"), "definedName"))
        cpart = self.sheet_part(COUNTS)
        self.set_text(cpart, in_elem(self.text(cpart), "f"))
        return new_last_row

    def fix_sst_count(self):
        """sharedStrings/@count is the number of cells that use shared strings;
        keep it honest after cells were converted to inline strings."""
        if "xl/sharedStrings.xml" not in self.parts:
            return
        n = sum(len(re.findall(r'<c [^>]*t="s"', self.text(p))) for p in self.sheet_files.values())
        s = self.text("xl/sharedStrings.xml")
        s = re.sub(r'(<sst [^>]*?count=")\d+(")', r"\g<1>%d\2" % n, s, count=1)
        self.set_text("xl/sharedStrings.xml", s)

    # -- formulas on Counts
    def formula_cells(self, name=COUNTS):
        return {ref: c for ref, c in self.cells(name).items() if c.formula}

    def recompute(self, name=COUNTS):
        """Evaluate every formula on `name` and return {ref: (cached, computed)}."""
        ev = Evaluator(self, name)
        out = {}
        for ref, c in self.formula_cells(name).items():
            out[ref] = (c.value, ev.eval_cell(ref))
        return out

    def patch_cached(self, name=COUNTS):
        """Rewrite stale cached <v> values of formulas; return list of (ref, old, new)."""
        changes = []
        part = self.sheet_part(name)
        xml = self.text(part)
        for ref, (cached, computed) in self.recompute(name).items():
            new = fmt_number(computed) if not isinstance(computed, str) else computed
            if cached == new:
                continue
            pat = re.compile(r'(<c r="%s"[^>]*>(?:<f>.*?</f>|<f[^>]*/>))(?:<v>.*?</v>)?(</c>)' % ref, re.S)
            m = pat.search(xml)
            if not m:
                raise WorkbookError("cannot find formula cell %s in %s" % (ref, part))
            xml = xml[:m.start()] + m.group(1) + "<v>%s</v>" % xml_escape(new) + m.group(2) + xml[m.end():]
            changes.append((ref, cached, new))
        if changes:
            self.set_text(part, xml)
        return changes

    # -- saving
    def save(self, out_path):
        """Write the zip with the original entry order and metadata; changed
        parts are re-deflated, untouched parts are copied as-is."""
        tmp = out_path + ".tmp"
        with zipfile.ZipFile(self.path) as src, zipfile.ZipFile(tmp, "w") as dst:
            for info in self.infos:
                data = self.parts[info.filename]
                zi = zipfile.ZipInfo(info.filename, date_time=info.date_time)
                zi.compress_type = info.compress_type
                zi.external_attr = info.external_attr
                zi.create_system = info.create_system
                dst.writestr(zi, data)
        os.replace(tmp, out_path)


# ---------------------------------------------------------- evaluator ----

class Evaluator:
    """Tiny evaluator for the formula shapes used on the Counts tab."""

    TOK = re.compile(r"""\s*(?:
        (?P<num>\d+(?:\.\d+)?)|
        (?P<str>"(?:[^"]|"")*")|
        (?P<ref>(?:'[^']+'|[A-Za-z_][\w.]*)!\$?[A-Z]{1,3}\$?\d+(?::\$?[A-Z]{1,3}\$?\d+)?|\$?[A-Z]{1,3}\$?\d+(?::\$?[A-Z]{1,3}\$?\d+)?)|
        (?P<name>[A-Z][A-Z0-9_.]*)|
        (?P<op><>|<=|>=|[-+*/=<>(),])
        )""", re.X)

    def __init__(self, wb, sheet):
        self.wb = wb
        self.sheet = sheet
        self.memo = {}

    def eval_cell(self, ref, sheet=None):
        sheet = sheet or self.sheet
        key = (sheet, ref)
        if key in self.memo:
            return self.memo[key]
        c = self.wb.cells(sheet).get(ref)
        if c is None or c.kind == "blank":
            val = None
        elif c.formula:
            val = self.eval(c.formula, sheet)
        elif c.kind == "n":
            val = float(c.value)
        else:
            val = c.value
        self.memo[key] = val
        return val

    def range_values(self, sheet, a, b):
        c1, r1 = split_ref(a)
        c2, r2 = split_ref(b)
        out = []
        for r in range(r1, r2 + 1):
            for ci in range(col_to_idx(c1), col_to_idx(c2) + 1):
                out.append(self.eval_cell("%s%d" % (idx_to_col(ci), r), sheet))
        return out

    # -- parser
    def eval(self, formula, sheet):
        self.toks = []
        pos = 0
        while pos < len(formula):
            m = self.TOK.match(formula, pos)
            if not m or m.end() == pos:
                raise FormulaError("cannot tokenize formula at %r" % formula[pos:])
            pos = m.end()
            self.toks.append((m.lastgroup, m.group(m.lastgroup)))
        self.i = 0
        self.cur_sheet = sheet
        v = self.p_compare()
        if self.i != len(self.toks):
            raise FormulaError("trailing tokens in formula %r" % formula)
        return v

    def peek(self):
        return self.toks[self.i] if self.i < len(self.toks) else (None, None)

    def take(self, kind=None, val=None):
        k, v = self.peek()
        if (kind and k != kind) or (val and v != val):
            raise FormulaError("expected %s %s, got %s %s" % (kind, val, k, v))
        self.i += 1
        return v

    def p_compare(self):
        left = self.p_add()
        while self.peek() == ("op", "=") or self.peek() == ("op", "<>"):
            op = self.take("op")
            right = self.p_add()
            left = self.elementwise(lambda a, b: self.equal(a, b) if op == "=" else not self.equal(a, b), left, right)
        return left

    def p_add(self):
        left = self.p_mul()
        while self.peek() in (("op", "+"), ("op", "-")):
            op = self.take("op")
            right = self.p_mul()
            left = self.elementwise(lambda a, b: self.num(a) + self.num(b) if op == "+" else self.num(a) - self.num(b), left, right)
        return left

    def p_mul(self):
        left = self.p_atom()
        while self.peek() in (("op", "*"), ("op", "/")):
            op = self.take("op")
            right = self.p_atom()
            left = self.elementwise(lambda a, b: self.num(a) * self.num(b) if op == "*" else self.num(a) / self.num(b), left, right)
        return left

    def p_atom(self):
        k, v = self.peek()
        if k == "num":
            self.take()
            return float(v)
        if k == "str":
            self.take()
            return v[1:-1].replace('""', '"')
        if k == "op" and v == "(":
            self.take()
            inner = self.p_compare()
            self.take("op", ")")
            return inner
        if k == "op" and v == "-":
            self.take()
            return self.elementwise(lambda a, b: -self.num(a), self.p_atom(), 0.0)
        if k == "ref":
            self.take()
            return self.ref_value(v)
        if k == "name":
            self.take()
            self.take("op", "(")
            args = []
            if self.peek() != ("op", ")"):
                args.append(self.p_compare())
                while self.peek() == ("op", ","):
                    self.take()
                    args.append(self.p_compare())
            self.take("op", ")")
            return self.call(v, args)
        raise FormulaError("unexpected token %s %r" % (k, v))

    def ref_value(self, text):
        sheet = self.cur_sheet
        if "!" in text:
            sheet, text = text.split("!", 1)
            sheet = sheet.strip("'")
        text = text.replace("$", "")
        if ":" in text:
            a, b = text.split(":")
            return self.range_values(sheet, a, b)
        return self.eval_cell(text, sheet)

    # -- functions
    def call(self, name, args):
        if name == "COUNTA":
            return float(sum(1 for a in args for x in self.aslist(a) if x not in (None, "")))
        if name == "COUNTIF":
            rng, crit = args
            return float(sum(1 for x in self.aslist(rng) if self.match_crit(x, crit)))
        if name == "SUMPRODUCT":
            arrays = [self.aslist(a) for a in args]
            total = 0.0
            for vals in zip(*arrays):
                p = 1.0
                for v in vals:
                    p *= self.num(v)
                total += p
            return total
        if name == "SUM":
            return float(sum(self.num(x) for a in args for x in self.aslist(a)))
        raise FormulaError("function %s is not supported by this evaluator" % name)

    # -- helpers
    @staticmethod
    def aslist(v):
        return v if isinstance(v, list) else [v]

    @staticmethod
    def num(v):
        if v is None:
            return 0.0
        if isinstance(v, bool):
            return 1.0 if v else 0.0
        if isinstance(v, (int, float)):
            return float(v)
        try:
            return float(v)
        except ValueError:
            raise FormulaError("#VALUE! cannot use %r as a number" % v)

    @staticmethod
    def equal(a, b):
        if a is None:
            a = "" if isinstance(b, str) else 0.0 if b is not None else None
        if b is None:
            b = "" if isinstance(a, str) else 0.0 if a is not None else None
        if isinstance(a, str) and isinstance(b, str):
            return a.casefold() == b.casefold()
        if isinstance(a, str) or isinstance(b, str):
            return False
        return float(a or 0) == float(b or 0)

    def match_crit(self, x, crit):
        if isinstance(crit, list):
            crit = crit[0]
        if crit is None:
            crit = ""
        if isinstance(crit, str):
            m = re.match(r"(<>|<=|>=|=|<|>)(.*)", crit)
            if m:
                op, rest = m.groups()
                try:
                    rest = float(rest)
                except ValueError:
                    pass
                if op == "=":
                    return self.equal(x, rest)
                if op == "<>":
                    return not self.equal(x, rest)
                if x is None or isinstance(x, str) != isinstance(rest, str):
                    return False
                a, b = (x.casefold(), rest.casefold()) if isinstance(x, str) else (float(x), float(rest))
                return {"<": a < b, "<=": a <= b, ">": a > b, ">=": a >= b}[op]
            if x is None:
                return crit == ""
            return isinstance(x, str) and x.casefold() == crit.casefold()
        return x is not None and not isinstance(x, str) and float(x) == float(crit)

    @staticmethod
    def elementwise(fn, a, b):
        if isinstance(a, list) or isinstance(b, list):
            la = a if isinstance(a, list) else [a] * len(b)
            lb = b if isinstance(b, list) else [b] * len(a)
            if len(la) != len(lb):
                raise FormulaError("array size mismatch")
            return [fn(x, y) for x, y in zip(la, lb)]
        return fn(a, b)


# -------------------------------------------------------------- csv -------

def csv_text(rows, title_line=None, trailing_newline=True):
    import io
    buf = io.StringIO()
    if title_line is not None:
        buf.write(title_line + "\n")
    w = csv.writer(buf, lineterminator="\n")
    w.writerows(rows)
    s = buf.getvalue()
    if not trailing_newline and s.endswith("\n"):
        s = s[:-1]
    return s


def sheet_csv_path(data_dir, xlsx_path, sheet):
    stem = os.path.splitext(os.path.basename(xlsx_path))[0]
    return os.path.join(data_dir, "%s_%s.csv" % (stem, sheet))


def export_text(wb, sheet, xlsx_path):
    """The exact text of one sheet's CSV export, in the repo's convention:
    every row 1..max_row and column 1..max_col, LF line endings, minimal
    quoting, hyperlinked cells exported as their URL. Two legacy quirks are
    reproduced so that the exports match the committed files byte for byte:
    the Screening export starts with a line holding the file stem
    (LVR_screening_sheet_2_Screening) and has no trailing newline."""
    stem = os.path.splitext(os.path.basename(xlsx_path))[0]
    rows = wb.grid(sheet)
    if sheet == SCREENING:
        return csv_text(rows, title_line="%s_%s" % (stem, sheet), trailing_newline=False)
    return csv_text(rows)


def die(msg, code=1):
    print("error: %s" % msg, file=sys.stderr)
    sys.exit(code)
