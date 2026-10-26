#!/usr/bin/env python3
"""Write a GRADE Summary of Findings table for diagnostic test accuracy
(Schunemann 2008 BMJ; GRADE Handbook, diagnostic tests chapter; Schunemann
2020 J Clin Epidemiol parts 21 and 22) as Markdown.

For each index test x reference standard it shows pooled sensitivity and
specificity, number of studies and participants, and, for each stated
pre-test probability (prevalence), the true/false positives/negatives per
1000 people tested with their 95% CI ranges, plus the certainty of evidence
rated across risk of bias, indirectness, inconsistency, imprecision and
publication bias, with lettered footnotes.

Numbers come from the command line (one entry), from an entries JSON (several
entries; see --entries-schema) or from a dta-meta-analysis results.json
(--results-json, read tolerantly: it looks for sensitivity/specificity
estimates with CIs anywhere in the file).

The certainty rating is arithmetic on the domain judgements you supply; it
does not judge the evidence for you. See references/grade_dta.md for the
rules and when a Summary of Findings table is not appropriate.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LEVELS = ["very low", "low", "moderate", "high"]
SYMBOLS = {"high": "⊕⊕⊕⊕", "moderate": "⊕⊕⊕◯",
           "low": "⊕⊕◯◯", "very low": "⊕◯◯◯"}
DOMAINS = ["risk_of_bias", "indirectness", "inconsistency", "imprecision", "publication_bias"]
DOMAIN_LABEL = {"risk_of_bias": "Risk of bias", "indirectness": "Indirectness",
                "inconsistency": "Inconsistency", "imprecision": "Imprecision",
                "publication_bias": "Publication bias"}
DOWNGRADE = {"not serious": 0, "none": 0, "undetected": 0, "serious": 1, "suspected": 1,
             "strongly suspected": 1, "very serious": 2}

SPEC_SCHEMA = {
    "question": "Should {index test} be used to identify adults who need low vision rehabilitation?",
    "population": "Adults attending {setting}",
    "prevalences": [0.1, 0.3, 0.5],
    "entries": [
        {
            "index_test": "Two screening questions (restaurant menu, keyboard)",
            "reference_standard": "Measured visual acuity worse than 6/12",
            "threshold": "either question answered 'no'",
            "sensitivity": [0.80, 0.70, 0.88],
            "specificity": [0.75, 0.65, 0.83],
            "studies": 4,
            "participants": 1234,
            "design": "cross-sectional",
            "start": "high",
            "ratings": {"risk_of_bias": "serious", "indirectness": "not serious",
                        "inconsistency": "serious", "imprecision": "not serious",
                        "publication_bias": "undetected"},
            "ratings_specificity": {"_comment": "optional: overrides for the TN/FP rows"},
            "footnotes": {"risk_of_bias": "Two of four studies used a case-control design (QUADAS-2 patient selection).",
                          "inconsistency": "Sensitivity ranged from 0.55 to 0.92 with non-overlapping CIs."},
            "results_json": "paper/dta/two_questions/results.json",
            "_comment": "results_json is optional; when present it supplies sensitivity/specificity/studies/participants",
        }
    ],
}


# --------------------------------------------------------------------------
# Reading pooled estimates from a results.json written by another skill
# --------------------------------------------------------------------------

def _walk(obj, path=()):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _walk(v, path + (str(k).lower(),))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk(v, path + (str(i),))
    else:
        yield path, obj


def _triplet(node) -> list[float] | None:
    """Turn {'estimate':..,'ci_low':..,'ci_high':..} or [est, lo, hi] into [est, lo, hi]."""
    if isinstance(node, (int, float)):
        return [float(node), float("nan"), float("nan")]
    if isinstance(node, list) and len(node) == 3 and all(isinstance(x, (int, float)) for x in node):
        return [float(x) for x in node]
    if isinstance(node, dict):
        low = {k.lower(): v for k, v in node.items()}
        est = next((low[k] for k in ("estimate", "est", "pooled", "value", "mean", "point") if k in low), None)
        lo = next((low[k] for k in ("ci_low", "ci_lower", "lower", "lcl", "low", "ci95_low") if k in low), None)
        hi = next((low[k] for k in ("ci_high", "ci_upper", "upper", "ucl", "high", "ci95_high") if k in low), None)
        ci = next((low[k] for k in ("ci", "ci95", "95%ci", "ci_95") if k in low), None)
        if isinstance(ci, (list, tuple)) and len(ci) == 2:
            lo, hi = ci
        if est is not None:
            return [float(est), float(lo) if lo is not None else float("nan"),
                    float(hi) if hi is not None else float("nan")]
    return None


def from_results_json(path: Path, analysis: str | None) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    node = data
    if analysis:
        found = None
        for container in (data, data.get("analyses", {}) if isinstance(data, dict) else {}):
            if isinstance(container, dict) and analysis in container:
                found = container[analysis]
                break
        if found is None:
            sys.exit(f"{path}: analysis {analysis!r} not found; top-level keys: {list(data)[:20]}")
        node = found
    out = {}
    if isinstance(node, dict):
        low = {k.lower(): v for k, v in node.items()}
        if "pooled" in low and low["pooled"] is None:
            sys.exit(f"{path}: 'pooled' is null, i.e. dta-meta-analysis decided not to pool (k < 4, mixed "
                     "thresholds or reference standards). A Summary of Findings from pooled estimates is not "
                     "appropriate; use a per-study table and rate certainty narratively (references/grade_dta.md).")

        def flat_triplet(d: dict, stem: str):
            """dta_pool.py layout: sens, sens_lo, sens_hi side by side in one dict."""
            if stem in d and isinstance(d[stem], (int, float)):
                lo, hi = d.get(f"{stem}_lo"), d.get(f"{stem}_hi")
                if isinstance(lo, (int, float)) and isinstance(hi, (int, float)):
                    return [float(d[stem]), float(lo), float(hi)]
            return None

        for key, names in (("sensitivity", ("sensitivity", "sens", "pooled_sensitivity", "sens_pooled")),
                           ("specificity", ("specificity", "spec", "pooled_specificity", "spec_pooled"))):
            stem = "sens" if key == "sensitivity" else "spec"
            for container in [low] + [{k.lower(): v for k, v in low[sub].items()}
                                      for sub in ("summary", "pooled", "bivariate", "estimates", "results")
                                      if isinstance(low.get(sub), dict)]:
                t = flat_triplet(container, stem)
                if t is None:
                    t = next((_triplet(container[n]) for n in names
                              if n in container and _triplet(container[n]) is not None), None)
                if t is not None:
                    out[key] = t
                    break
        for key, names in (("studies", ("k", "n_studies", "studies", "num_studies")),
                           ("participants", ("n", "n_participants", "participants", "total_n", "n_total"))):
            for n in names:
                v = low.get(n)
                if isinstance(v, (int, float)):
                    out[key] = int(v)
                    break
                if isinstance(v, list):
                    out[key] = len(v)
                    break
    if "participants" not in out:
        # dta_pool.py writes per_study.csv (TP, FP, FN, TN per study) next to results.json
        per_study = path.parent / "per_study.csv"
        if per_study.exists():
            import csv
            total = 0
            with per_study.open(newline="", encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    try:
                        total += sum(int(float(row[c])) for c in ("TP", "FP", "FN", "TN"))
                    except (KeyError, ValueError):
                        total = None
                        break
            if total:
                out["participants"] = total
    missing = [k for k in ("sensitivity", "specificity") if k not in out]
    if missing:
        sys.exit(f"{path}: could not find pooled {', '.join(missing)} with a CI; pass --sens/--spec by hand "
                 "(keys tried: pooled.sens/sens_lo/sens_hi, sensitivity/sens with estimate + ci_low/ci_high, "
                 "or [est, lo, hi])")
    return out


# --------------------------------------------------------------------------
# GRADE arithmetic
# --------------------------------------------------------------------------

def certainty(start: str, ratings: dict) -> tuple[str, int]:
    start = start.lower().strip()
    if start not in LEVELS:
        sys.exit(f"start certainty must be one of {LEVELS}, got {start!r}")
    level = LEVELS.index(start)
    for d in DOMAINS:
        r = str(ratings.get(d, "not serious")).lower().strip().replace("-", " ")
        if r not in DOWNGRADE:
            sys.exit(f"rating for {d} must be one of {sorted(DOWNGRADE)}, got {r!r}")
        level -= DOWNGRADE[r]
    level = max(level, 0)
    return LEVELS[level], level


def per_1000(p: float, est: float, lo: float, hi: float, *, positive: bool, with_condition: bool):
    """Count per 1000 tested. positive=True gives the 'correct' cell (TP or TN)."""
    base = 1000 * (p if with_condition else 1 - p)
    if positive:
        vals = (base * est, base * lo, base * hi)
    else:
        vals = (base * (1 - est), base * (1 - hi), base * (1 - lo))
    return tuple(None if v != v else int(round(v)) for v in vals)   # NaN -> None


def fmt_cell(vals) -> str:
    est, lo, hi = vals
    if lo is None or hi is None:
        return f"{est}"
    return f"{est} ({lo} to {hi})"


def fmt_prop(t) -> str:
    est, lo, hi = t
    if lo != lo or hi != hi:
        return f"{est:.2f}"
    return f"{est:.2f} (95% CI {lo:.2f} to {hi:.2f})"


# --------------------------------------------------------------------------
# Markdown
# --------------------------------------------------------------------------

class Footnotes:
    def __init__(self):
        self.items: list[str] = []

    def mark(self, text: str | None) -> str:
        if not text:
            return ""
        if text not in self.items:
            self.items.append(text)
        return "^" + chr(ord("a") + self.items.index(text))


def entry_rows(e: dict, prevalences: list[float], fn: Footnotes) -> list[str]:
    sens, spec = e["sensitivity"], e["specificity"]
    k, n = e.get("studies", "?"), e.get("participants", "?")
    design = e.get("design", "cross-sectional")
    r_sens = {d: e.get("ratings", {}).get(d, "not serious") for d in DOMAINS}
    r_spec = dict(r_sens)
    r_spec.update({d: v for d, v in (e.get("ratings_specificity") or {}).items() if not d.startswith("_")})
    notes = e.get("footnotes", {})
    c_sens, _ = certainty(e.get("start", "high"), r_sens)
    c_spec, _ = certainty(e.get("start", "high"), r_spec)

    def domain_cells(r: dict) -> str:
        cells = []
        for d in DOMAINS:
            cells.append(f"{r[d]}{fn.mark(notes.get(d)) if DOWNGRADE.get(str(r[d]).lower().replace('-', ' '), 0) else ''}")
        return " | ".join(cells)

    rows = []
    kinds = [("True positives (people with the condition who are correctly identified)", True, True, sens, r_sens, c_sens),
             ("False negatives (people with the condition who are missed)", False, True, sens, r_sens, c_sens),
             ("True negatives (people without the condition who are correctly identified)", True, False, spec, r_spec, c_spec),
             ("False positives (people without the condition wrongly classified as having it)", False, False, spec, r_spec, c_spec)]
    for label, positive, with_cond, prop, r, cert in kinds:
        cells = [fmt_cell(per_1000(p, prop[0], prop[1], prop[2], positive=positive, with_condition=with_cond))
                 for p in prevalences]
        rows.append(f"| {label} | {k} ({n}) | {design} | {domain_cells(r)} | " + " | ".join(cells)
                    + f" | {SYMBOLS[cert]} {cert.upper()} |")
    return rows


def build_markdown(spec: dict) -> str:
    prevalences = [float(p) for p in spec.get("prevalences", [0.1, 0.3, 0.5])]
    if any(not 0 < p < 1 for p in prevalences):
        sys.exit("prevalences must be proportions between 0 and 1")
    fn = Footnotes()
    md = ["# Summary of findings (GRADE, diagnostic test accuracy)", ""]
    if spec.get("question"):
        md += [f"**Question:** {spec['question']}", ""]
    if spec.get("population"):
        md += [f"**Population and setting:** {spec['population']}", ""]
    md += [f"**Pre-test probabilities (prevalence of the target condition) used:** "
           + ", ".join(f"{p:.0%}" for p in prevalences)
           + " {state where each comes from, e.g. prevalence in the included studies, a glaucoma clinic series}", ""]
    for e in spec["entries"]:
        md += [f"## {e.get('index_test', '{index test}')} vs {e.get('reference_standard', '{reference standard}')}", ""]
        md += [f"**Index test:** {e.get('index_test', '{index test}')}"
               + (f" (positive if {e['threshold']})" if e.get("threshold") else ""),
               f"**Reference standard:** {e.get('reference_standard', '{reference standard}')}",
               f"**Pooled sensitivity:** {fmt_prop(e['sensitivity'])}; **pooled specificity:** {fmt_prop(e['specificity'])}"
               f" ({e.get('studies', '?')} studies, {e.get('participants', '?')} participants)"
               + (f"; source `{e['results_json']}`" if e.get("results_json") else ""), ""]
        head = ("| Outcome | No. of studies (participants) | Study design | Risk of bias | Indirectness | "
                "Inconsistency | Imprecision | Publication bias | "
                + " | ".join(f"Per 1000 at {p:.0%}" for p in prevalences) + " | Certainty |")
        sep = "|---|---|---|---|---|---|---|---|" + "---:|" * len(prevalences) + "---|"
        md += [head, sep] + entry_rows(e, prevalences, fn) + [""]
    md += ["**Certainty symbols:** " + "; ".join(f"{SYMBOLS[l]} {l}" for l in reversed(LEVELS)), ""]
    if fn.items:
        md += ["**Explanations:**", ""]
        md += [f"^{chr(ord('a') + i)} {t}" for i, t in enumerate(fn.items)] + [""]
    md += ["_Each cell gives the number per 1000 people tested, with the range implied by the 95% CI of the pooled "
           "sensitivity (TP, FN) or specificity (TN, FP). Certainty starts at "
           + "/".join(sorted({e.get('start', 'high') for e in spec['entries']}))
           + " and is lowered one level per 'serious' and two per 'very serious' judgement (references/grade_dta.md)._", ""]
    return "\n".join(md)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--entries", type=Path, help="JSON describing one or more index test x reference standard entries")
    p.add_argument("--entries-schema", action="store_true", help="print an example entries JSON and exit")
    p.add_argument("--results-json", type=Path, help="dta-meta-analysis results.json to take sens/spec/k/n from")
    p.add_argument("--analysis", help="name of the analysis inside --results-json, if it holds several")
    p.add_argument("--index-test", default="{index test}")
    p.add_argument("--reference", default="{reference standard}", help="reference standard")
    p.add_argument("--threshold", help="positivity threshold of the index test")
    p.add_argument("--sens", type=float, nargs="+", metavar="EST [LO HI]", help="pooled sensitivity and 95%% CI")
    p.add_argument("--spec", dest="spec_vals", type=float, nargs="+", metavar="EST [LO HI]",
                   help="pooled specificity and 95%% CI")
    p.add_argument("--studies", type=int)
    p.add_argument("--participants", type=int)
    p.add_argument("--design", default="cross-sectional")
    p.add_argument("--start", default="high", choices=LEVELS, help="starting certainty (default: high)")
    for d in DOMAINS:
        p.add_argument(f"--{d.replace('_', '-')}", default="not serious",
                       help=f"{DOMAIN_LABEL[d]} judgement: not serious | serious | very serious"
                            + (" | undetected | strongly suspected" if d == "publication_bias" else ""))
    p.add_argument("--footnote", action="append", default=[], metavar="DOMAIN=TEXT",
                   help="reason for a downgrade, e.g. risk_of_bias='two case-control studies'; repeatable")
    p.add_argument("--prevalence", type=float, nargs="+", default=[0.1, 0.3, 0.5],
                   help="pre-test probabilities as proportions (default: 0.1 0.3 0.5)")
    p.add_argument("--question")
    p.add_argument("--population")
    p.add_argument("--out", type=Path, default=Path("paper/sof/summary_of_findings.md"),
                   help="output Markdown (default: %(default)s)")
    a = p.parse_args(argv)

    if a.entries_schema:
        print(json.dumps(SPEC_SCHEMA, indent=2, ensure_ascii=False))
        return 0

    if a.entries:
        spec = json.loads(a.entries.read_text(encoding="utf-8"))
        if "entries" not in spec:
            sys.exit("entries JSON needs an 'entries' list (see --entries-schema)")
        for e in spec["entries"]:
            if e.get("results_json"):
                e.update(from_results_json(Path(e["results_json"]), e.get("analysis")))
            for key in ("sensitivity", "specificity"):
                if key not in e:
                    sys.exit(f"entry {e.get('index_test', '?')!r} has no {key}")
                e[key] = _pad(e[key], key)
    else:
        e = {"index_test": a.index_test, "reference_standard": a.reference, "threshold": a.threshold,
             "design": a.design, "start": a.start,
             "ratings": {d: getattr(a, d) for d in DOMAINS}, "footnotes": {}}
        if a.results_json:
            e.update(from_results_json(a.results_json, a.analysis))
            e["results_json"] = str(a.results_json)
        if a.sens:
            e["sensitivity"] = _pad(a.sens, "sensitivity")
        if a.spec_vals:
            e["specificity"] = _pad(a.spec_vals, "specificity")
        if a.studies is not None:
            e["studies"] = a.studies
        if a.participants is not None:
            e["participants"] = a.participants
        for key in ("sensitivity", "specificity"):
            if key not in e:
                sys.exit(f"no {key}: pass --sens/--spec EST LO HI, --results-json or --entries")
        for item in a.footnote:
            d, _, text = item.partition("=")
            d = d.strip().replace("-", "_")
            if d not in DOMAINS:
                sys.exit(f"--footnote domain must be one of {DOMAINS}, got {d!r}")
            e["footnotes"][d] = text.strip()
        spec = {"question": a.question, "population": a.population, "prevalences": a.prevalence, "entries": [e]}

    md = build_markdown(spec)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(md, encoding="utf-8")
    for e in spec["entries"]:
        c, _ = certainty(e.get("start", "high"), e.get("ratings", {}))
        print(f"{e.get('index_test')} vs {e.get('reference_standard')}: sens {fmt_prop(e['sensitivity'])}, "
              f"spec {fmt_prop(e['specificity'])}, certainty {c}")
    print(f"wrote {a.out}")
    return 0


def _pad(vals, name: str) -> list[float]:
    vals = [float(v) for v in vals]
    if len(vals) == 1:
        vals += [float("nan"), float("nan")]
    if len(vals) != 3:
        sys.exit(f"{name} needs EST or EST LO HI, got {vals}")
    est, lo, hi = vals
    if not 0 <= est <= 1 or (lo == lo and not (0 <= lo <= est)) or (hi == hi and not (est <= hi <= 1)):
        sys.exit(f"{name} = {vals}: need 0 <= LO <= EST <= HI <= 1 (proportions, not percentages)")
    return vals


if __name__ == "__main__":
    sys.exit(main())
