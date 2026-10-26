#!/usr/bin/env python3
"""Rate measurement-property results against the COSMIN criteria for good
measurement properties (Prinsen et al. 2018, Table 1), summarise them per
instrument x property across studies, and grade the quality of the summarised
evidence with the COSMIN modified GRADE approach (Prinsen 2018, Table 4).

Input: a CSV with one row per reported result
  study_id, instrument, property, statistic, value, n  (required)
  label, subscale, ci_low, ci_high, model, mic, hypothesis, confirmed,
  indirectness, override, override_reason, page, notes   (optional)

Output (in --out-dir, default analysis/instruments/):
  property_ratings.csv        one row per input result with its rating (+ - ?)
  study_property_ratings.csv  one row per study x instrument x property
  summary_of_findings.csv/.md one row per instrument x property across studies:
                              k, total n, range, summary rating (+ - ? +-),
                              risk-of-bias summary, GRADE downgrades, certainty

Rules: references/criteria_good_measurement_properties.md (assets) and the
"Modified GRADE rule set" section of references/cosmin_sr.md. Ratings are
advisory; the reviewer confirms each one and may use the `override` column
(with `override_reason`) to record a judgement the rules cannot make.

Run with `python3 -I` because the CSVs are data, not code. Standard library only.

Examples
  python3 -I rate_properties.py analysis/instruments/property_results.csv \\
      --rob analysis/risk_of_bias/cosmin_ratings.csv --out-dir analysis/instruments
  python3 -I rate_properties.py results.csv --structural-ok "GAL-9" --majority 0.75
"""
from __future__ import annotations

import argparse
import csv
import math
import os
import re
import sys
from collections import OrderedDict, defaultdict

PROPERTIES = [
    "Structural validity", "Internal consistency", "Cross-cultural validity",
    "Reliability", "Measurement error", "Criterion validity",
    "Hypotheses testing", "Responsiveness",
]
PROP_SYNONYMS = {
    "structural validity": "Structural validity", "dimensionality": "Structural validity",
    "factor structure": "Structural validity", "unidimensionality": "Structural validity",
    "internal consistency": "Internal consistency", "homogeneity": "Internal consistency",
    "cross-cultural validity": "Cross-cultural validity", "cross cultural validity": "Cross-cultural validity",
    "measurement invariance": "Cross-cultural validity", "dif": "Cross-cultural validity",
    "cross-cultural validity / measurement invariance": "Cross-cultural validity",
    "reliability": "Reliability", "test-retest": "Reliability", "test-retest reliability": "Reliability",
    "test retest reliability": "Reliability", "inter-rater reliability": "Reliability",
    "intra-rater reliability": "Reliability", "retest": "Reliability",
    "measurement error": "Measurement error", "agreement": "Measurement error",
    "criterion validity": "Criterion validity", "concurrent validity": "Criterion validity",
    "hypotheses testing": "Hypotheses testing", "hypothesis testing": "Hypotheses testing",
    "construct validity": "Hypotheses testing", "convergent validity": "Hypotheses testing",
    "known-groups validity": "Hypotheses testing", "known groups validity": "Hypotheses testing",
    "discriminative validity": "Hypotheses testing",
    "hypotheses testing for construct validity": "Hypotheses testing",
    "responsiveness": "Responsiveness", "sensitivity to change": "Responsiveness",
}

SYMBOL = {"+": "sufficient", "-": "insufficient", "?": "indeterminate", "+-": "inconsistent"}
ROB_RANK = {"very good": 0, "adequate": 1, "doubtful": 2, "inadequate": 3}
GRADE_LEVELS = ["High", "Moderate", "Low", "Very low"]
REQUIRED = ["study_id", "instrument", "property", "statistic", "value", "n"]

# ---------------------------------------------------------------- parsing helpers

_DASH = re.compile(r"\s*(?:-|–|—|to)\s*")


def norm(s: str) -> str:
    s = (s or "").strip().casefold().replace("’", "'")
    s = re.sub(r"cronbach'?s?\s*", "cronbach ", s)
    s = re.sub(r"[_]", " ", s)
    return " ".join(s.split())


def parse_value(raw: str):
    """Return ('num', x) | ('range', (lo, hi)) | ('frac', (a, b)) | ('yes'|'no'|'na', None) | ('text', raw)."""
    s = (raw or "").strip()
    if s == "":
        return ("na", None)
    low = s.casefold()
    if low in ("nr", "na", "n/a", "not reported", "-"):
        return ("na", None)
    if low in ("yes", "y", "true", "met", "confirmed", "none", "no violation", "not violated", "no important dif", "no dif", "adequate"):
        return ("yes", None)
    if low in ("no", "n", "false", "not met", "violated", "rejected", "important dif", "inadequate", "not confirmed"):
        return ("no", None)
    m = re.fullmatch(r"\s*(\d+)\s*/\s*(\d+)\s*", s)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return ("frac", (a, b))
    pct = s.endswith("%")
    core = s.rstrip("%").strip()
    try:
        x = float(core)
        return ("num", x / 100.0 if pct else x)
    except ValueError:
        pass
    parts = _DASH.split(core)
    if len(parts) == 2:
        try:
            lo, hi = float(parts[0]), float(parts[1])
            return ("range", (min(lo, hi), max(lo, hi)))
        except ValueError:
            pass
    return ("text", s)


def num_or_none(raw: str):
    try:
        return float((raw or "").strip())
    except ValueError:
        return None


def in_band(v, lo, hi) -> bool:
    kind, x = v
    if kind == "num":
        return lo <= x <= hi
    if kind == "range":
        return lo <= x[0] and x[1] <= hi
    return False


def ge(v, thr) -> bool | None:
    kind, x = v
    if kind == "num":
        return x >= thr
    if kind == "range":
        return x[0] >= thr
    return None


def lt(v, thr) -> bool | None:
    kind, x = v
    if kind == "num":
        return x < thr
    if kind == "range":
        return x[1] < thr
    return None


def absval(v):
    kind, x = v
    if kind == "num":
        return ("num", abs(x))
    if kind == "range":
        a, b = abs(x[0]), abs(x[1])
        return ("range", (min(a, b), max(a, b)))
    return v


# ---------------------------------------------------------------- hypothesis parsing

_HYP = re.compile(
    r"^\s*(?P<abs>\|?|abs\s*)?\s*(?P<var>[a-z0-9 ._]*?)\s*\|?\s*"
    r"(?P<op>>=|=>|≥|>|<=|=<|≤|<|between|in)\s*(?P<a>-?\d*\.?\d+)"
    r"(?:\s*(?:and|-|–|,)\s*(?P<b>-?\d*\.?\d+))?\s*$", re.I)


def hypothesis_confirmed(hyp: str, value) -> bool | None:
    """Evaluate a hypothesis string such as '>=0.30', '|r|>0.5', 'between 0.3 and 0.5',
    '<0.3', 'r 0.3-0.5' against the parsed value. None when it cannot be evaluated."""
    h = (hyp or "").strip()
    if not h:
        return None
    kind, x = value
    if kind not in ("num", "range"):
        return None
    v = x if kind == "num" else (x[0] + x[1]) / 2.0
    m = _HYP.match(h)
    if not m:
        m2 = re.fullmatch(r"\s*(-?\d*\.?\d+)\s*(?:-|–|to)\s*(-?\d*\.?\d+)\s*", h)
        if m2:
            a, b = float(m2.group(1)), float(m2.group(2))
            return min(a, b) <= v <= max(a, b)
        return None
    use_abs = bool(m.group("abs")) or "|" in h or "abs" in h.casefold()
    if use_abs:
        v = abs(v)
    op, a, b = m.group("op"), float(m.group("a")), m.group("b")
    if op in (">=", "=>", "≥"):
        return v >= a
    if op == ">":
        return v > a
    if op in ("<=", "=<", "≤"):
        return v <= a
    if op == "<":
        return v < a
    if op in ("between", "in") and b is not None:
        b = float(b)
        return min(a, b) <= v <= max(a, b)
    return None


# ---------------------------------------------------------------- statistic classification

def classify(stat: str, prop: str) -> tuple[str, str]:
    """Map a statistic name to (family, aspect). Families drive the rating rules."""
    s = norm(stat)
    s = s.replace("coefficient", "").replace("mean square", "mnsq").strip()
    s = " ".join(s.split())
    # structural validity aspects
    if re.search(r"\b(cfi|tli|nnfi|comparative fit|tucker)\b", s):
        return ("fit_index_high", "unidimensionality")
    if re.search(r"\brmsea\b", s):
        return ("rmsea", "unidimensionality")
    if re.search(r"\bsrmr\b", s):
        return ("srmr", "unidimensionality")
    if "unidimension" in s or "pca of residual" in s or "first contrast" in s or "variance explained" in s:
        return ("unidim_statement", "unidimensionality")
    if "residual correlation" in s or "local independence" in s or re.search(r"\bq3\b", s):
        return ("local_independence", "local independence")
    if "scalab" in s or "loevinger" in s or "monotonic" in s:
        return ("monotonicity", "monotonicity")
    if re.search(r"\b(infit|outfit)\b", s):
        if "zstd" in s or "z-std" in s or "z std" in s or re.search(r"\bz\b", s):
            return ("fit_zstd", "model fit")
        return ("fit_mnsq", "model fit")
    if "chi" in s and ("p" in s.split() or "p-value" in s or "p value" in s or s.endswith(" p")):
        return ("fit_chi_p", "model fit")
    if s in ("efa", "exploratory factor analysis", "pca", "principal component"):
        return ("efa_only", "unidimensionality")
    # internal consistency
    if "alpha" in s or "omega" in s or re.search(r"\bkr[- ]?20\b", s) or "kuder" in s:
        return ("alpha", "")
    if "person separation reliability" in s or "person reliability" in s or re.search(r"\bpsi\b", s) or "irt reliability" in s or "rasch reliability" in s or "separation reliability" in s:
        return ("psr", "")
    if "person separation" in s or "separation index" in s or s in ("separation", "person separation index", "g"):
        return ("psi_index", "")
    # reliability
    if re.search(r"\bicc\b", s) or "intraclass" in s:
        return ("icc", "")
    if "kappa" in s:
        return ("kappa", "")
    # measurement error
    if re.search(r"\bsdc\b", s) or "smallest detectable" in s or "mdc" in s or "minimal detectable" in s:
        return ("sdc", "")
    if re.search(r"\bloa\b", s) or "limits of agreement" in s:
        return ("loa", "")
    if re.search(r"\bsem\b", s) or "standard error of measurement" in s:
        return ("sem", "")
    # accuracy / correlation
    if re.search(r"\bauc\b", s) or "area under" in s or "c-statistic" in s:
        return ("auc", "")
    if "sensitivity" in s or "specificity" in s or "ppv" in s or "npv" in s or "likelihood ratio" in s:
        return ("sens_spec", "")
    if "hypotheses confirmed" in s or "hypothesis confirmed" in s or "proportion confirmed" in s or "% confirmed" in s:
        return ("hyp_fraction", "")
    if "dif" in s.split() or "differential item" in s or "mcfadden" in s or "invariance" in s:
        if "mcfadden" in s or "r2" in s or "r²" in s:
            return ("dif_r2", "")
        return ("dif", "")
    if "effect size" in s or re.search(r"\bsrm\b", s) or "cohen" in s or "standardi[sz]ed response mean" in s:
        return ("effect_size", "")
    if "pearson" in s or "spearman" in s or "correlation" in s or re.fullmatch(r"r|rho|r\s*\(.*\)", s):
        if "test-retest" in s or "retest" in s or "test retest" in s:
            return ("retest_corr", "")
        return ("correlation", "")
    if "test-retest" in s or "retest" in s:
        return ("retest_corr", "")
    if "known group" in s or "group difference" in s or "mean difference" in s or "anova" in s or "t-test" in s or "regression" in s or "odds ratio" in s:
        return ("group_diff", "")
    return ("unknown", "")


# ---------------------------------------------------------------- row-level rating

def rate_row(r: dict, prop: str, structural_ok_fn) -> tuple[str, str, str, str]:
    """Return (rating, reason, aspect, family). Rating is '+', '-', '?' or 'info'."""
    fam, aspect = classify(r.get("statistic", ""), prop)
    v = parse_value(r.get("value", ""))
    hyp = (r.get("hypothesis") or "").strip()
    conf = norm(r.get("confirmed", ""))
    mic = num_or_none(r.get("mic", ""))

    if prop == "Structural validity":
        if fam == "efa_only":
            return ("?", "EFA/PCA alone cannot meet the 2018 criterion (CFA or IRT/Rasch needed)", aspect, fam)
        if fam == "fit_index_high":
            g = ge(v, 0.95)
            return ("+" if g else "-" if g is False else "?", "CFI/TLI > 0.95", aspect, fam) if g is not None else ("?", "value not numeric", aspect, fam)
        if fam == "rmsea":
            g = lt(v, 0.06)
            return ("+" if g else "-" if g is False else "?", "RMSEA < 0.06", aspect, fam)
        if fam == "srmr":
            g = lt(v, 0.08)
            return ("+" if g else "-" if g is False else "?", "SRMR < 0.08", aspect, fam)
        if fam == "unidim_statement":
            if v[0] == "yes":
                return ("+", "author-reported unidimensionality (comparable measure; reviewer confirms)", aspect, fam)
            if v[0] == "no":
                return ("-", "unidimensionality violated", aspect, fam)
            return ("?", "unidimensionality statement not yes/no", aspect, fam)
        if fam == "local_independence":
            if v[0] in ("yes", "no"):
                return ("+" if v[0] == "yes" else "-", "local independence (author statement)", aspect, fam)
            thr = 0.37 if re.search(r"\bq3\b", norm(r.get("statistic", ""))) else 0.20
            g = lt(absval(v), thr)
            return ("+" if g else "-" if g is False else "?", f"residual correlation < {thr}", aspect, fam)
        if fam == "monotonicity":
            if v[0] in ("yes", "no"):
                return ("+" if v[0] == "yes" else "-", "monotonicity (author statement)", aspect, fam)
            g = ge(v, 0.30)
            return ("+" if g else "-" if g is False else "?", "item scalability > 0.30", aspect, fam)
        if fam == "fit_mnsq":
            if v[0] in ("num", "range"):
                ok = in_band(v, 0.5, 1.5)
                return ("+" if ok else "-", "infit/outfit MNSQ within 0.5-1.5 for all items", aspect, fam)
            if v[0] in ("yes", "no"):
                return ("+" if v[0] == "yes" else "-", "model fit (author statement)", aspect, fam)
            return ("?", "fit value not numeric", aspect, fam)
        if fam == "fit_zstd":
            ok = in_band(v, -2.0, 2.0) if v[0] in ("num", "range") else None
            return ("+" if ok else "-" if ok is False else "?", "Z-standardised fit within -2..2", aspect, fam)
        if fam == "fit_chi_p":
            g = ge(v, 0.01)
            return ("+" if g else "-" if g is False else "?", "IRT model fit chi-square p > 0.01", aspect, fam)
        return ("info", "statistic not used by the structural-validity criterion", aspect, fam)

    if prop == "Internal consistency":
        if fam == "psi_index":
            k, x = v
            if k == "num":
                rel = x * x / (1 + x * x)
                v = ("num", rel)
                r["_cmp"] = rel
                r["_derived"] = f"person separation index {x:g} -> reliability {rel:.2f} (G^2/(1+G^2))"
            else:
                return ("?", "person separation index not numeric", aspect, fam)
            fam = "psr"
        if fam in ("alpha", "psr"):
            g = ge(v, 0.70)
            if g is None:
                return ("?", "value not numeric", aspect, fam)
            ok, why = structural_ok_fn(r["instrument"])
            if not ok:
                return ("?", f"criterion 'at least low evidence for sufficient structural validity' not met ({why}); alpha/PSR {'>=' if g else '<'} 0.70", aspect, fam)
            return ("+" if g else "-", f"alpha/PSR >= 0.70 per unidimensional (sub)scale; structural validity {why}", aspect, fam)
        return ("info", "statistic not used by the internal-consistency criterion", aspect, fam)

    if prop == "Reliability":
        if fam in ("icc", "kappa"):
            g = ge(v, 0.70)
            return ("+" if g else "-" if g is False else "?", "ICC or weighted kappa >= 0.70", aspect, fam)
        if fam in ("retest_corr", "correlation"):
            return ("?", "ICC or weighted kappa not reported (a Pearson/Spearman correlation ignores systematic change)", aspect, fam)
        return ("?", "ICC or weighted kappa not reported", aspect, fam)

    if prop == "Measurement error":
        if fam == "sem" and mic is not None and v[0] == "num":
            sdc = 1.96 * math.sqrt(2) * v[1]
            r["_derived"] = f"SDC = 1.96*sqrt(2)*SEM = {sdc:.3g}"
            r["_cmp"] = sdc
            v = ("num", sdc)
            fam = "sdc"
        if fam in ("sdc", "loa"):
            if mic is None:
                return ("?", "MIC not defined, so SDC/LoA cannot be compared with it", aspect, fam)
            g = lt(absval(v), mic)
            return ("+" if g else "-" if g is False else "?", f"SDC or LoA < MIC ({mic:g})", aspect, fam)
        if fam == "sem":
            return ("?", "SEM reported without MIC", aspect, fam)
        return ("?", "SDC, LoA or SEM not reported", aspect, fam)

    if prop == "Criterion validity":
        if fam in ("correlation", "retest_corr", "auc"):
            g = ge(absval(v), 0.70)
            return ("+" if g else "-" if g is False else "?", "correlation with gold standard >= 0.70 or AUC >= 0.70", aspect, fam)
        if fam == "sens_spec":
            return ("?", "sensitivity/specificity alone are not rated by COSMIN; report AUC here, and take the accuracy to the QUADAS-2 / DTA path", aspect, fam)
        return ("?", "not all information for '+' reported", aspect, fam)

    if prop in ("Hypotheses testing", "Responsiveness"):
        if fam == "hyp_fraction":
            k, x = v
            frac = x if k == "num" else (x[0] / x[1] if k == "frac" and x[1] else None)
            if frac is None:
                return ("?", "fraction of confirmed hypotheses not numeric", aspect, fam)
            r["_frac"] = frac
            return ("+" if frac >= 0.75 else "-", "at least 75% of hypotheses confirmed", aspect, fam)
        if prop == "Responsiveness" and fam == "auc" and not hyp and conf == "":
            g = ge(v, 0.70)
            return ("+" if g else "-" if g is False else "?", "AUC (changed vs not changed) >= 0.70", aspect, fam)
        if conf in ("yes", "y", "true", "confirmed"):
            return ("+", "hypothesis confirmed (stated by reviewer)", aspect, fam)
        if conf in ("no", "n", "false", "rejected", "not confirmed"):
            return ("-", "hypothesis not confirmed (stated by reviewer)", aspect, fam)
        if hyp:
            c = hypothesis_confirmed(hyp, v)
            if c is None:
                return ("?", f"hypothesis '{hyp}' could not be evaluated against value '{r.get('value')}'", aspect, fam)
            return ("+" if c else "-", f"hypothesis '{hyp}' {'confirmed' if c else 'not confirmed'}", aspect, fam)
        return ("?", "no a-priori hypothesis stated, so the result cannot be rated (COSMIN: '?')", aspect, fam)

    if prop == "Cross-cultural validity":
        if fam == "dif_r2":
            g = lt(v, 0.02)
            return ("+" if g else "-" if g is False else "?", "no important DIF (McFadden R2 < 0.02)", aspect, fam)
        if fam == "dif":
            if v[0] == "yes":
                return ("+", "no important DIF / no important group differences", aspect, fam)
            if v[0] == "no":
                return ("-", "important DIF or group differences", aspect, fam)
            if v[0] in ("num", "frac"):
                return ("?", "number of DIF items given; the reviewer judges whether the DIF is important (use override)", aspect, fam)
        return ("?", "DIF / multi-group analysis not reported", aspect, fam)

    return ("?", "unknown property", aspect, fam)


# ---------------------------------------------------------------- aggregation

def combine_study(prop: str, rows: list[dict], model_hint: str) -> tuple[str, str]:
    """Combine the rated rows of one study x instrument x property into one rating."""
    rated = [r for r in rows if r["rating"] in ("+", "-", "?")]
    if not rated:
        return ("?", "no rateable statistic")
    if prop == "Structural validity":
        aspects = defaultdict(list)
        for r in rated:
            aspects[r["aspect"] or "other"].append(r["rating"])
        if any("-" in v for v in aspects.values()):
            bad = [a for a, v in aspects.items() if "-" in v]
            return ("-", "criterion violated for: " + ", ".join(bad))
        fams = {r["family"] for r in rated}
        irt = model_hint in ("rasch", "irt") or fams & {"fit_mnsq", "fit_zstd", "fit_chi_p", "local_independence", "monotonicity"}
        if model_hint in ("efa", "pca"):
            return ("?", "EFA/PCA only")
        if irt:
            needed = ["unidimensionality", "local independence", "monotonicity", "model fit"]
            have = {a for a, v in aspects.items() if "+" in v}
            missing = [a for a in needed if a not in have]
            if missing:
                return ("?", "Rasch/IRT: not all information for '+' reported; missing " + ", ".join(missing))
            return ("+", "Rasch/IRT: unidimensionality, local independence, monotonicity and model fit all adequate")
        if "+" in aspects.get("unidimensionality", []):
            return ("+", "CFA: at least one fit index meets the criterion")
        return ("?", "not all information for '+' reported")
    ratings = [r["rating"] for r in rated]
    if prop in ("Hypotheses testing", "Responsiveness"):
        fr = [r for r in rated if r.get("_frac") is not None]
        if fr:
            frac = fr[0]["_frac"]
            return ("+" if frac >= 0.75 else "-", f"{frac:.0%} of hypotheses confirmed")
        auc_rows = [r for r in rated if r["family"] == "auc" and r["rating"] in ("+", "-")]
        hyp_rows = [r for r in rated if r["rating"] in ("+", "-") and r["family"] != "auc"]
        if hyp_rows:
            k = sum(1 for r in hyp_rows if r["rating"] == "+")
            frac = k / len(hyp_rows)
            return ("+" if frac >= 0.75 else "-", f"{k}/{len(hyp_rows)} hypotheses confirmed ({frac:.0%})")
        if auc_rows:
            return (auc_rows[0]["rating"], "AUC criterion")
        return ("?", "no a-priori hypotheses")
    if "-" in ratings:
        return ("-", "at least one (sub)scale or result below the criterion")
    if "+" in ratings and "?" not in ratings:
        return ("+", "all results meet the criterion")
    if "+" in ratings:
        return ("?", "some results indeterminate; " + "; ".join(sorted({r["reason"] for r in rated if r["rating"] == "?"})))
    return ("?", "; ".join(sorted({r["reason"] for r in rated})))


def summarise(ratings: list[str], majority: float | None) -> tuple[str, str, bool]:
    """Summarise study ratings across studies: returns (rating, note, inconsistent_flag)."""
    definite = [x for x in ratings if x in ("+", "-")]
    if not definite:
        return ("?", "all results indeterminate", False)
    plus = definite.count("+")
    minus = definite.count("-")
    if minus == 0:
        return ("+", f"{plus} sufficient" + (f", {len(ratings) - plus} indeterminate (ignored)" if len(ratings) > plus else ""), False)
    if plus == 0:
        return ("-", f"{minus} insufficient" + (f", {len(ratings) - minus} indeterminate (ignored)" if len(ratings) > minus else ""), False)
    if majority is not None:
        if plus / len(definite) >= majority:
            return ("+", f"{plus}/{len(definite)} sufficient (majority rule {majority:.0%}; inconsistency remains and is downgraded)", True)
        if minus / len(definite) >= majority:
            return ("-", f"{minus}/{len(definite)} insufficient (majority rule {majority:.0%}; inconsistency remains and is downgraded)", True)
    return ("+-", f"inconsistent: {plus} sufficient, {minus} insufficient; explore an explanation (population, language, mode) before accepting '+-'", True)


def rob_downgrade(rob_list: list[str]) -> tuple[int, str]:
    """Prinsen 2018 Table 4 risk-of-bias rule, applied to the COSMIN RoB ratings of the contributing studies."""
    known = [x for x in rob_list if x in ROB_RANK]
    if not known:
        return (0, "not rated")
    good = sum(1 for x in known if ROB_RANK[x] <= 1)
    doubt = sum(1 for x in known if x == "doubtful")
    inad = sum(1 for x in known if x == "inadequate")
    if good >= 2:
        return (0, "multiple studies of very good/adequate quality")
    if good == 1:
        return (-1, "only one study of adequate quality (serious)")
    if doubt >= 2:
        return (-1, "multiple studies of doubtful quality (serious)")
    if doubt == 1:
        return (-2, "only one study of doubtful quality (very serious)")
    if inad >= 2:
        return (-2, "multiple studies of inadequate quality (very serious)")
    return (-3, "only one study of inadequate quality (extremely serious)")


def imprecision_downgrade(total_n: float) -> tuple[int, str]:
    if total_n < 50:
        return (-2, f"total n = {total_n:g} < 50 (very serious)")
    if total_n <= 100:
        return (-1, f"total n = {total_n:g} in 50-100 (serious)")
    return (0, f"total n = {total_n:g} > 100")


INDIRECT = {"": 0, "none": 0, "no": 0, "serious": -1, "very serious": -2}


def grade(down: int) -> str:
    return GRADE_LEVELS[min(-down, 3)]


# ---------------------------------------------------------------- IO

def read_csv(path: str) -> tuple[list[str], list[dict]]:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rd = csv.DictReader(fh, restkey="_extra")
        fields = [f.strip() for f in (rd.fieldnames or [])]
        rows = []
        for i, r in enumerate(rd, start=2):
            if r.get("_extra"):
                sys.exit(f"ERROR: {path} line {i} has {len(fields) + len(r['_extra'])} fields but the header has {len(fields)} (unquoted comma?)")
            rows.append({(k or "").strip(): (v or "").strip() for k, v in r.items() if k != "_extra"})
    return fields, rows


def md_escape(s: str) -> str:
    return (s or "").replace("|", "\\|").replace("\n", " ")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("csv", help="measurement-property results CSV (see assets/property_results_template.csv)")
    p.add_argument("--rob", help="risk-of-bias cosmin_ratings.csv from the risk-of-bias skill (study_id, instrument, measurement_property, overall_rating)")
    p.add_argument("--out-dir", default="analysis/instruments")
    p.add_argument("--by", help="extra grouping column (e.g. language, population) for the summary; COSMIN: summarise per subgroup when inconsistency is explained")
    p.add_argument("--majority", type=float, default=None, help="fraction (e.g. 0.75) above which a mixed +/- set is summarised by the majority instead of '+-'; off by default")
    p.add_argument("--structural-ok", action="append", default=[], metavar="INSTRUMENT", help="assert at least low evidence for sufficient structural validity from outside the CSV (cite the source in Methods); unlocks internal consistency ratings")
    p.add_argument("--indirectness", action="append", default=[], metavar="INSTRUMENT=serious|very serious", help="indirectness downgrade per instrument (default none; the reviewer judges population/setting match)")
    p.add_argument("--check", action="store_true", help="validate the input and print the row ratings; write nothing")
    args = p.parse_args(argv)

    if not os.path.isfile(args.csv):
        print(f"ERROR: no such file: {args.csv}", file=sys.stderr)
        return 2
    fields, rows = read_csv(args.csv)
    missing = [c for c in REQUIRED if c not in fields]
    if missing:
        print("ERROR: missing required column(s): " + ", ".join(missing), file=sys.stderr)
        return 1
    errors = []
    for i, r in enumerate(rows, start=2):
        if not r["study_id"] or not r["instrument"]:
            errors.append(f"line {i}: empty study_id or instrument")
        prop = PROP_SYNONYMS.get(norm(r["property"]))
        if prop is None:
            errors.append(f"line {i}: unknown property '{r['property']}' (allowed: {', '.join(PROPERTIES)})")
        r["_prop"] = prop
        if r["n"] and num_or_none(r["n"]) is None and r["n"].upper() != "NR":
            errors.append(f"line {i}: n is not a number: '{r['n']}'")
        ov = r.get("override", "")
        if ov and ov not in ("+", "-", "?"):
            errors.append(f"line {i}: override must be +, - or ?, got '{ov}'")
        if ov and not r.get("override_reason"):
            errors.append(f"line {i}: override without override_reason")
    if errors:
        print("ERROR:\n  " + "\n  ".join(errors), file=sys.stderr)
        return 1

    indirect = {}
    for item in args.indirectness:
        if "=" not in item:
            print(f"ERROR: --indirectness expects INSTRUMENT=serious|very serious, got '{item}'", file=sys.stderr)
            return 1
        k, v = item.split("=", 1)
        if v.strip().casefold() not in INDIRECT:
            print(f"ERROR: indirectness level must be none, serious or very serious, got '{v}'", file=sys.stderr)
            return 1
        indirect[k.strip()] = v.strip().casefold()

    rob = {}
    rob_unmatched = []
    if args.rob:
        if not os.path.isfile(args.rob):
            print(f"ERROR: no such file: {args.rob}", file=sys.stderr)
            return 2
        rfields, rrows = read_csv(args.rob)
        need = ["study_id", "instrument", "measurement_property", "overall_rating"]
        miss = [c for c in need if c not in rfields]
        if miss:
            print("ERROR: --rob file lacks column(s): " + ", ".join(miss), file=sys.stderr)
            return 1
        for r in rrows:
            prop = PROP_SYNONYMS.get(norm(r["measurement_property"]))
            if prop is None:
                continue
            rob[(r["study_id"], norm(r["instrument"]), prop)] = norm(r["overall_rating"])

    # --- first pass: structural validity per study, so internal consistency can check it
    groups: "OrderedDict[tuple, list]" = OrderedDict()
    for r in rows:
        key = (r["study_id"], r["instrument"], r["_prop"])
        groups.setdefault(key, []).append(r)

    structural_by_instrument: dict[str, list[str]] = defaultdict(list)
    study_results: "OrderedDict[tuple, dict]" = OrderedDict()

    def dummy_ok(_inst):
        return (False, "pending")

    for key, grp in groups.items():
        if key[2] != "Structural validity":
            continue
        for r in grp:
            rating, reason, aspect, fam = rate_row(r, "Structural validity", dummy_ok)
            r.update({"rating": rating, "reason": reason, "aspect": aspect, "family": fam})
        model_hint = norm(next((r.get("model", "") for r in grp if r.get("model")), ""))
        rating, reason = combine_study("Structural validity", grp, model_hint)
        ov = next((r for r in grp if r.get("override")), None)
        if ov:
            rating, reason = ov["override"], f"OVERRIDE ({ov['override_reason']}); rule said {rating}: {reason}"
        study_results[key] = {"rating": rating, "reason": reason, "rows": grp}
        structural_by_instrument[norm(key[1])].append(rating)

    asserted = {norm(x) for x in args.structural_ok}

    def structural_ok(inst: str):
        if norm(inst) in asserted:
            return (True, "asserted by --structural-ok (cite the source)")
        rs = structural_by_instrument.get(norm(inst), [])
        if "+" in rs:
            return (True, "sufficient in at least one study in this CSV")
        if "-" in rs:
            return (False, "structural validity rated insufficient")
        return (False, "no structural validity evidence in this CSV; use --structural-ok if it exists elsewhere")

    # --- second pass: everything else
    for key, grp in groups.items():
        if key[2] == "Structural validity":
            continue
        for r in grp:
            rating, reason, aspect, fam = rate_row(r, key[2], structural_ok)
            r.update({"rating": rating, "reason": reason, "aspect": aspect, "family": fam})
        rating, reason = combine_study(key[2], grp, "")
        ov = next((r for r in grp if r.get("override")), None)
        if ov:
            rating, reason = ov["override"], f"OVERRIDE ({ov['override_reason']}); rule said {rating}: {reason}"
        study_results[key] = {"rating": rating, "reason": reason, "rows": grp}

    # n per study x property: max n over its rows (rows of one study share participants)
    for key, res in study_results.items():
        ns = [num_or_none(r["n"]) for r in res["rows"]]
        ns = [x for x in ns if x is not None]
        res["n"] = max(ns) if ns else None
        res["label"] = next((r.get("label", "") for r in res["rows"] if r.get("label")), "")
        res["rob"] = rob.get((key[0], norm(key[1]), key[2]), "")
        if args.rob and not res["rob"]:
            rob_unmatched.append(key)
        byv = next((r.get(args.by, "") for r in res["rows"] if args.by and r.get(args.by)), "") if args.by else ""
        res["by"] = byv

    # --- summary per instrument x property (x by)
    summary: "OrderedDict[tuple, dict]" = OrderedDict()
    for key, res in study_results.items():
        skey = (key[1], key[2], res["by"])
        summary.setdefault(skey, []).append((key[0], res))

    sof_rows = []
    for (inst, prop, byv), items in summary.items():
        ratings = [res["rating"] for _, res in items]
        srating, snote, inconsistent = summarise(ratings, args.majority)
        # total n and risk of bias count only the studies whose result is + or -;
        # indeterminate results do not contribute to the summarised evidence
        definitive = [(sid, res) for sid, res in items if res["rating"] in ("+", "-")] or items
        total_n = sum(res["n"] for _, res in definitive if res["n"] is not None)
        n_missing = sum(1 for _, res in definitive if res["n"] is None)
        robs = [res["rob"] for _, res in definitive]
        per_study = "; ".join(f"{sid}{(' ' + res['label']) if res['label'] else ''}: {res['rating']} (n={res['n']:g}{', RoB ' + res['rob'] if res['rob'] else ''})" if res["n"] is not None else f"{sid}: {res['rating']} (n=NR)" for sid, res in items)
        # descriptive range per statistic family (never across families: an alpha and a
        # person-separation index are not on one scale; hypotheses are not comparable at all)
        desc = ""
        if prop not in ("Hypotheses testing", "Responsiveness"):
            fams: "OrderedDict[str, list]" = OrderedDict()
            for _, res in items:
                for r in res["rows"]:
                    if r["rating"] not in ("+", "-"):
                        continue
                    pv = parse_value(r["value"])
                    if r.get("_cmp") is not None:
                        pv = ("num", r["_cmp"])
                    if pv[0] == "num":
                        fams.setdefault(r["family"], []).append((pv[1], num_or_none(r["n"]) or 0.0))
            parts = []
            for fam, vals in fams.items():
                lo, hi = min(v[0] for v in vals), max(v[0] for v in vals)
                rng = f"{lo:.2f}" if lo == hi else f"{lo:.2f} to {hi:.2f}"
                wsum = sum(v[1] for v in vals)
                label = {"psr": "reliability (alpha/PSR)", "alpha": "alpha/omega", "icc": "ICC", "kappa": "kappa",
                         "auc": "AUC", "correlation": "r", "sdc": "SDC", "loa": "LoA", "dif_r2": "DIF R2",
                         "fit_index_high": "CFI/TLI", "rmsea": "RMSEA", "srmr": "SRMR", "local_independence": "residual r",
                         "monotonicity": "scalability", "fit_mnsq": "infit/outfit", "fit_zstd": "fit Z", "fit_chi_p": "chi2 p"}.get(fam, fam)
                parts.append(f"{label} {rng}" + (f" (n-weighted mean {sum(v[0] * v[1] for v in vals) / wsum:.2f}, descriptive)" if len(vals) > 1 and wsum else ""))
            desc = "; ".join(parts)
        if srating == "?":
            cert, downs = "not graded (indeterminate)", ""
            d_rob = d_inc = d_imp = d_ind = 0
            rob_note = imp_note = ""
        else:
            d_rob, rob_note = rob_downgrade(robs) if args.rob else (0, "no --rob file: risk of bias not applied")
            d_inc = -1 if inconsistent else 0
            d_imp, imp_note = imprecision_downgrade(total_n) if not n_missing or total_n else (-2, "n not reported")
            d_ind = INDIRECT[indirect.get(inst, "none")]
            total_down = d_rob + d_inc + d_imp + d_ind
            cert = grade(total_down) + ("" if args.rob else " (RoB not applied)")
            downs = f"RoB {d_rob:+d}; inconsistency {d_inc:+d}; imprecision {d_imp:+d}; indirectness {d_ind:+d}"
        sof_rows.append({
            "instrument": inst, "property": prop, **({args.by: byv} if args.by else {}),
            "k": len(definitive) if srating != "?" else len(items),
            "k_indeterminate": sum(1 for _, res in items if res["rating"] == "?"),
            "total_n": f"{total_n:g}" if total_n else "NR",
            "results": desc, "per_study": per_study,
            "summary_rating": srating, "summary_word": SYMBOL[srating], "summary_note": snote,
            "rob_ratings": "; ".join(x or "unrated" for x in robs), "rob_judgement": rob_note if srating != "?" else "",
            "downgrades": downs, "imprecision": imp_note if srating != "?" else "",
            "indirectness": indirect.get(inst, "none"), "quality_of_evidence": cert,
        })

    # --- print / write
    if args.check:
        for key, res in study_results.items():
            print(f"{key[0]} | {key[1]} | {key[2]} | {res['rating']} | {res['reason']}")
            for r in res["rows"]:
                print(f"    {r['statistic']} = {r['value']} -> {r['rating']} ({r['reason']})")
        print(f"OK: {len(rows)} results, {len(study_results)} study x instrument x property, {len(sof_rows)} summary rows")
        if rob_unmatched:
            print(f"WARNING: no COSMIN RoB rating matched for {len(rob_unmatched)} study x instrument x property: " + "; ".join(f"{k[0]}/{k[1]}/{k[2]}" for k in rob_unmatched))
        return 0

    os.makedirs(args.out_dir, exist_ok=True)
    out1 = os.path.join(args.out_dir, "property_ratings.csv")
    extra = [c for c in fields if c not in REQUIRED]
    with open(out1, "w", newline="", encoding="utf-8") as fh:
        cols = REQUIRED + extra + ["rating", "rating_word", "rule", "derived"]
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            row = {c: r.get(c, "") for c in REQUIRED + extra}
            row.update({"rating": r["rating"], "rating_word": SYMBOL.get(r["rating"], r["rating"]), "rule": r["reason"], "derived": r.get("_derived", "")})
            w.writerow(row)
    out2 = os.path.join(args.out_dir, "study_property_ratings.csv")
    with open(out2, "w", newline="", encoding="utf-8") as fh:
        cols = ["study_id", "label", "instrument", "property"] + ([args.by] if args.by else []) + ["n", "rating", "rating_word", "reason", "cosmin_rob"]
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for key, res in study_results.items():
            row = {"study_id": key[0], "label": res["label"], "instrument": key[1], "property": key[2],
                   "n": f"{res['n']:g}" if res["n"] is not None else "NR", "rating": res["rating"],
                   "rating_word": SYMBOL[res["rating"]], "reason": res["reason"], "cosmin_rob": res["rob"]}
            if args.by:
                row[args.by] = res["by"]
            w.writerow(row)
    out3 = os.path.join(args.out_dir, "summary_of_findings.csv")
    with open(out3, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(sof_rows[0].keys()) if sof_rows else ["instrument"])
        w.writeheader()
        w.writerows(sof_rows)
    out4 = os.path.join(args.out_dir, "summary_of_findings.md")
    lines = ["# Summary of findings: measurement properties (COSMIN)", "",
             f"Source: `{args.csv}`" + (f", risk of bias from `{args.rob}`" if args.rob else ", risk of bias not supplied (certainty not downgraded for it)") + ".",
             "Ratings: + sufficient, - insufficient, ? indeterminate, +- inconsistent (Prinsen 2018 Table 1). "
             "Quality of evidence: modified GRADE (Prinsen 2018 Table 4): start High; risk of bias, inconsistency, imprecision (total n 50-100 = -1, < 50 = -2), indirectness. "
             "Indeterminate summaries are not graded. AI-drafted ratings are advisory; the reviewer confirms each row.", "",
             "| Instrument | Property" + (f" | {args.by}" if args.by else "") + " | k | Total n | Results | Per study | Summary | Quality of evidence | Downgrades |",
             "|---|---|" + ("---|" if args.by else "") + "---|---|---|---|---|---|---|"]
    for s in sof_rows:
        lines.append("| " + " | ".join(md_escape(str(x)) for x in [
            s["instrument"], s["property"], *([s[args.by]] if args.by else []), s["k"], s["total_n"], s["results"], s["per_study"],
            f"{s['summary_rating']} ({s['summary_word']})", s["quality_of_evidence"],
            "; ".join(x for x in [s["downgrades"], s["rob_judgement"], s["imprecision"], s["summary_note"] if s["summary_rating"] == "+-" or "majority" in s["summary_note"] else ""] if x)]) + " |")
    lines += ["", "## Per-study ratings", "", "| Study | Instrument | Property | n | Rating | Reason | COSMIN RoB |", "|---|---|---|---|---|---|---|"]
    for key, res in study_results.items():
        lines.append("| " + " | ".join(md_escape(str(x)) for x in [f"{key[0]} {res['label']}".strip(), key[1], key[2], f"{res['n']:g}" if res["n"] is not None else "NR", f"{res['rating']} ({SYMBOL[res['rating']]})", res["reason"], res["rob"] or ""]) + " |")
    with open(out4, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    print(f"Rated {len(rows)} results -> {len(study_results)} study x instrument x property -> {len(sof_rows)} summary rows")
    for s in sof_rows:
        print(f"  {s['instrument']} | {s['property']}{(' | ' + s[args.by]) if args.by else ''} | k={s['k']} n={s['total_n']} | {s['summary_rating']} | {s['quality_of_evidence']}")
    print("Wrote: " + ", ".join([out1, out2, out3, out4]))
    if rob_unmatched:
        print(f"WARNING: no COSMIN RoB rating matched for {len(rob_unmatched)} study x instrument x property (treated as unrated): " + "; ".join(f"{k[0]}/{k[1]}/{k[2]}" for k in rob_unmatched))
    inconsistent = [s for s in sof_rows if s["summary_rating"] == "+-"]
    if inconsistent:
        print(f"NOTE: {len(inconsistent)} inconsistent summary rating(s); look for an explanation (population, language, administration mode) and re-run with --by <column> if one exists.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
