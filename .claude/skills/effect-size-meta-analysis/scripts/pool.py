#!/usr/bin/env python3
"""Random-effects meta-analysis of non-2x2 outcomes (correlations, AUCs,
proportions, means, mean differences, SMDs, generic estimate/SE pairs).

Reads the effects.csv written by the data-extraction skill (or ad-hoc --row
input), pools one outcome type on the appropriate analysis scale, and writes
results.json, summary.md, per_study.csv, forest.svg/png (and funnel.svg/png,
loo.csv, subgroups.csv, metareg.csv when requested) to
<out>/<name>/.  See SKILL.md and references/methods.md for the methods and
when NOT to pool.

Examples
    python3 -I pool.py effects.csv --outcome correlation --name vfq_va \\
        --where instrument=VFQ-25 --where comparator=logMAR_VA --loo
    python3 -I pool.py --row "label=Smith 2019,estimate=0.42,n=110" \\
        --row "label=Lee 2021,estimate=0.51,n=80" --outcome correlation --name adhoc
    python3 -I pool.py effects.csv --outcome proportion --name lvr_need \\
        --transform logit --subgroup setting --egger
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import sys
from dataclasses import dataclass, field

try:
    import numpy as np
    from scipy import optimize, stats
except ImportError:  # python3 -I hides the user site; re-add that one trusted dir
    import site
    sys.path.append(site.getusersitepackages())
    try:
        import numpy as np
        from scipy import optimize, stats
    except ImportError:
        sys.exit("numpy/scipy/matplotlib are required: python3 -m pip install --user --break-system-packages numpy scipy matplotlib")

VERSION = "1.0.0"

OUTCOME_TYPES = {
    "correlation": "Pearson r (Fisher z scale)",
    "spearman": "Spearman rho (Fisher z scale, Bonett-Wright variance)",
    "auc": "Area under the ROC curve (natural or logit scale)",
    "proportion": "Proportion (logit or Freeman-Tukey double-arcsine scale)",
    "mean": "Raw mean (natural scale)",
    "md": "Mean difference (natural scale)",
    "smd": "Standardised mean difference, Hedges g",
    "generic": "Generic estimate with SE (natural scale)",
    # aliases accepted in outcome_type: mean_diff -> md; a `measure` column naming Spearman/rho makes a
    # correlation row spearman (data-extraction schema)
    "logratio": "Ratio measure (OR, RR, HR) pooled on the log scale",
}

MIN_K_FULL = 3          # below this no tau^2 / heterogeneity is meaningful
MIN_K_EGGER = 10        # Sterne 2011: funnel tests need >= 10 studies
MIN_K_PER_COVARIATE = 10  # Cochrane Handbook 10.11.5.1


class PoolError(Exception):
    pass


def warn(msg: str, store: list[str] | None = None) -> None:
    print(f"WARNING: {msg}", file=sys.stderr)
    if store is not None:
        store.append(msg)


# --------------------------------------------------------------------------
# Input handling
# --------------------------------------------------------------------------

def fnum(row: dict, key: str) -> float | None:
    v = row.get(key)
    if v is None:
        return None
    v = str(v).strip()
    if v == "" or v.upper() in {"NA", "N/A", "NR", "NONE", "NAN", "."}:
        return None
    try:
        return float(v)
    except ValueError:
        raise PoolError(f"column '{key}' has non-numeric value {v!r} in row {row.get('label') or row.get('study_id')}")


def read_rows(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        rows = []
        for r in reader:
            rows.append({(k or "").strip(): (v or "").strip() for k, v in r.items()})
    if not rows:
        raise PoolError(f"{path} has no data rows")
    return rows


def parse_adhoc_row(text: str) -> dict:
    """'label=Smith 2019,estimate=0.42,n=110' -> dict."""
    out = {}
    for part in text.split(","):
        if "=" not in part:
            raise PoolError(f"--row needs key=value pairs, got {part!r}")
        k, v = part.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def apply_where(rows: list[dict], clauses: list[str]) -> list[dict]:
    for clause in clauses:
        if "~" in clause and "=" not in clause.split("~", 1)[0]:
            col, pat = clause.split("~", 1)
            rx = re.compile(pat)
            rows = [r for r in rows if rx.search(r.get(col.strip(), "") or "")]
        elif "=" in clause:
            col, val = clause.split("=", 1)
            rows = [r for r in rows if (r.get(col.strip(), "") or "") == val.strip()]
        else:
            raise PoolError(f"--where must be col=value or col~regex, got {clause!r}")
    return rows


# --------------------------------------------------------------------------
# Transforms: natural scale <-> analysis scale
# --------------------------------------------------------------------------

@dataclass
class Scale:
    name: str                 # analysis-scale label
    natural: str              # natural-scale label
    fwd: object               # natural -> analysis
    back: object              # analysis -> natural
    log_axis: bool = False    # draw forest axis on a log scale


def _ci_to_se(low: float, high: float, level: float, fwd=lambda x: x) -> float:
    z = stats.norm.ppf(0.5 + level / 2)
    return (fwd(high) - fwd(low)) / (2 * z)


def identity_scale(natural="Estimate") -> Scale:
    return Scale("natural", natural, lambda x: x, lambda x: x)


def fisher_scale(natural="r") -> Scale:
    return Scale("Fisher z", natural, np.arctanh, np.tanh)


def logit_scale(natural="Proportion") -> Scale:
    return Scale("logit", natural, lambda p: np.log(p / (1 - p)), lambda y: 1 / (1 + np.exp(-y)))


def log_scale(natural="Ratio") -> Scale:
    return Scale("log", natural, np.log, np.exp, log_axis=True)


def ftt_scale(n_harmonic: float) -> Scale:
    """Freeman-Tukey double arcsine with Miller (1978) back-transform using
    the harmonic mean of the sample sizes (as metafor transf.ipft.hm)."""
    def back(t):
        t = np.asarray(t, dtype=float)
        n = n_harmonic
        # Miller 1978 inverse; clamp to the valid range of t
        tmin = 2 * math.asin(math.sqrt(0.5 / (n + 1)))
        tmax = 2 * math.asin(math.sqrt((n + 0.5) / (n + 1)))
        t = np.clip(t, tmin, tmax)
        p = 0.5 * (1 - np.sign(np.cos(t)) * np.sqrt(1 - (np.sin(t) + (np.sin(t) - 1 / np.sin(t)) / n) ** 2))
        return p
    return Scale("Freeman-Tukey double arcsine", "Proportion", None, back)


@dataclass
class Study:
    label: str
    study_id: str
    y: float          # analysis scale
    v: float          # variance on analysis scale
    n: float | None
    est_nat: float    # natural-scale point estimate as reported
    extra: dict = field(default_factory=dict)


def _n_from_groups(r: dict) -> float | None:
    n = fnum(r, "n")
    if n is None:
        n1, n2 = fnum(r, "n1"), fnum(r, "n2")
        if n1 is not None and n2 is not None:
            n = n1 + n2
        else:
            npos, nneg = fnum(r, "n_pos"), fnum(r, "n_neg")
            if npos is not None and nneg is not None:
                n = npos + nneg
    return n


def _direction(r: dict) -> float:
    d = (r.get("direction") or "").strip().lower()
    if d in {"-1", "neg", "negative", "flip", "reverse", "reversed"}:
        return -1.0
    return 1.0


def hanley_mcneil_se(auc: float, n_pos: float, n_neg: float) -> float:
    q1 = auc / (2 - auc)
    q2 = 2 * auc ** 2 / (1 + auc)
    var = (auc * (1 - auc) + (n_pos - 1) * (q1 - auc ** 2) + (n_neg - 1) * (q2 - auc ** 2)) / (n_pos * n_neg)
    return math.sqrt(var)


TYPE_ALIASES = {"mean_diff": "md", "mean_difference": "md", "pearson": "correlation", "r": "correlation",
                "rho": "spearman", "prevalence": "proportion", "hedges_g": "smd", "cohen_d": "smd",
                "log_or": "logratio", "or": "logratio", "rr": "logratio", "hr": "logratio"}


def load_studies_table(path: str | None, csv_path: str | None) -> dict[str, dict]:
    """studies.csv from the data-extraction skill (study_id, citation, cohort, ...), if present."""
    cand = path or (os.path.join(os.path.dirname(csv_path), "studies.csv") if csv_path else None)
    if not cand or not os.path.exists(cand):
        return {}
    with open(cand, newline="", encoding="utf-8-sig") as fh:
        return {(r.get("study_id") or "").strip(): r for r in csv.DictReader(fh)}


def normalise_rows(rows: list[dict], studies: dict[str, dict], warnings: list[str]) -> list[dict]:
    """Map data-extraction schema onto what build_studies expects: outcome_type aliases,
    Spearman detection from `measure`, labels and cohorts from studies.csv."""
    for r in rows:
        t = (r.get("outcome_type") or "").strip().lower()
        t = TYPE_ALIASES.get(t, t)
        measure = (r.get("measure") or "").lower()
        if t == "correlation" and re.search(r"spearman|\brho\b", measure):
            t = "spearman"
        if t == "correlation" and re.search(r"\bicc\b|kappa|intraclass", measure):
            warn(f"{r.get('label') or r.get('study_id')}: measure '{r.get('measure')}' is an agreement coefficient, not a "
                 "Pearson r; pool it only with other ICC/kappa values (use --where measure~ICC)", warnings)
        r["outcome_type"] = t
        sid = (r.get("study_id") or "").strip()
        st = studies.get(sid, {})
        if not r.get("label"):
            r["label"] = st.get("citation") or sid
            if r.get("subgroup"):
                r["label"] += f" ({r['subgroup']})"
        if st.get("cohort") and not r.get("cohort"):
            r["cohort"] = st["cohort"]
    return rows


def build_studies(rows: list[dict], outcome: str, level: float, args, warnings: list[str]):
    """Return (studies, scale, notes)."""
    studies: list[Study] = []
    notes: list[str] = []
    scale: Scale

    if outcome in ("correlation", "spearman"):
        scale = fisher_scale("r" if outcome == "correlation" else "rho")
    elif outcome == "auc":
        scale = logit_scale("AUC") if args.auc_scale == "logit" else identity_scale("AUC")
    elif outcome == "proportion":
        if args.transform == "ftt":
            ns = [_n_from_groups(r) for r in rows]
            if any(n is None for n in ns):
                raise PoolError("proportion with --transform ftt needs n for every row")
            n_h = len(ns) / sum(1 / n for n in ns)
            scale = ftt_scale(n_h)
            notes.append(f"Freeman-Tukey back-transform uses the harmonic mean n = {n_h:.1f} (Miller 1978; Barker 2021).")
        elif args.transform == "none":
            scale = identity_scale("Proportion")
        else:
            scale = logit_scale("Proportion")
    elif outcome in ("mean", "md", "generic"):
        scale = identity_scale({"mean": "Mean", "md": "Mean difference", "generic": "Estimate"}[outcome])
    elif outcome == "smd":
        scale = identity_scale("Hedges g")
    elif outcome == "logratio":
        scale = log_scale("Ratio")
    else:
        raise PoolError(f"unknown outcome type {outcome!r}; choose from {', '.join(OUTCOME_TYPES)}")

    for r in rows:
        label = r.get("label") or r.get("study_id") or f"row{len(studies)+1}"
        sid = r.get("study_id") or label
        est = fnum(r, "estimate")
        se = fnum(r, "se")
        lo, hi = fnum(r, "ci_low"), fnum(r, "ci_high")
        n = _n_from_groups(r)
        sign = _direction(r)
        y = v = None

        if outcome in ("correlation", "spearman"):
            if est is None:
                raise PoolError(f"{label}: correlation needs 'estimate'")
            if abs(est) >= 1:
                raise PoolError(f"{label}: |r| must be < 1")
            est *= sign
            y = float(np.arctanh(est))
            if n is not None and n > 3:
                v = 1 / (n - 3)
                if outcome == "spearman" or r.get("outcome_type") == "spearman":
                    v = (1 + est ** 2 / 2) / (n - 3)   # Bonett & Wright 2000
            elif se is not None:
                v = se ** 2
                notes.append(f"{label}: SE taken as given on the z scale (no n).")
            elif lo is not None and hi is not None:
                if sign < 0:
                    lo, hi = -hi, -lo
                v = _ci_to_se(lo, hi, level, np.arctanh) ** 2
            else:
                raise PoolError(f"{label}: correlation needs n (preferred), se, or a CI")

        elif outcome == "auc":
            if est is None:
                raise PoolError(f"{label}: auc needs 'estimate'")
            if not 0 < est < 1:
                raise PoolError(f"{label}: AUC must lie strictly between 0 and 1")
            if se is None:
                if lo is not None and hi is not None:
                    se = _ci_to_se(lo, hi, level)
                else:
                    npos, nneg = fnum(r, "n_pos"), fnum(r, "n_neg")
                    if npos is None:
                        npos = fnum(r, "n_positive")
                    if nneg is None and npos is not None and n is not None:
                        nneg = n - npos
                    if npos is None or nneg is None:
                        raise PoolError(f"{label}: auc needs se, a CI, or n_pos and n_neg (or n_positive and n) for Hanley-McNeil")
                    se = hanley_mcneil_se(est, npos, nneg)
                    notes.append(f"{label}: SE from Hanley & McNeil (1982) with n_pos={npos:g}, n_neg={nneg:g}.")
            if args.auc_scale == "logit":
                y = float(scale.fwd(est))
                v = (se / (est * (1 - est))) ** 2   # delta method
            else:
                y, v = est, se ** 2

        elif outcome == "proportion":
            events = fnum(r, "events")
            if events is None:
                events = fnum(r, "n_pos")
            if est is None and events is not None and n:
                est = events / n
            if est is None:
                raise PoolError(f"{label}: proportion needs 'estimate' or events + n")
            if events is None and n:
                events = round(est * n)
            if args.transform == "ftt":
                if n is None:
                    raise PoolError(f"{label}: ftt needs n")
                y = float(math.asin(math.sqrt(events / (n + 1))) + math.asin(math.sqrt((events + 1) / (n + 1))))
                v = 1 / (n + 0.5)
            elif args.transform == "none":
                y = est
                if se is not None:
                    v = se ** 2
                elif n:
                    if est in (0.0, 1.0):
                        pc = (events + 0.5) / (n + 1)
                        v = pc * (1 - pc) / (n + 1)
                        notes.append(f"{label}: 0 or 100% events; variance from a 0.5 continuity correction (consider --transform ftt).")
                    else:
                        v = est * (1 - est) / n
                else:
                    raise PoolError(f"{label}: proportion (no transform) needs se or n")
            else:  # logit
                if n is None and se is None and not (lo is not None and hi is not None):
                    raise PoolError(f"{label}: logit proportion needs n (preferred), se, or a CI")
                if n is not None:
                    e = events
                    if e == 0 or e == n:
                        e = e + 0.5 if e == 0 else e - 0.5
                        nn = n + 1
                        notes.append(f"{label}: 0 or 100% events; 0.5 continuity correction applied (consider --transform ftt).")
                    else:
                        nn = n
                    p = e / nn
                    y = math.log(p / (1 - p))
                    v = 1 / e + 1 / (nn - e)
                elif se is not None:
                    y = float(scale.fwd(est))
                    v = (se / (est * (1 - est))) ** 2
                else:
                    y = float(scale.fwd(est))
                    v = _ci_to_se(lo, hi, level, scale.fwd) ** 2

        elif outcome == "mean":
            if est is None:
                raise PoolError(f"{label}: mean needs 'estimate'")
            sd = fnum(r, "sd")
            if se is None:
                if sd is not None and n:
                    se = sd / math.sqrt(n)
                elif lo is not None and hi is not None:
                    se = _ci_to_se(lo, hi, level)
                else:
                    raise PoolError(f"{label}: mean needs se, sd + n, or a CI")
            y, v = est, se ** 2

        elif outcome in ("md", "smd"):
            m1, sd1, n1 = fnum(r, "m1"), fnum(r, "sd1"), fnum(r, "n1")
            m2, sd2, n2 = fnum(r, "m2"), fnum(r, "sd2"), fnum(r, "n2")
            have_groups = None not in (m1, sd1, n1, m2, sd2, n2)
            if outcome == "md":
                if have_groups:
                    est = m1 - m2
                    se = math.sqrt(sd1 ** 2 / n1 + sd2 ** 2 / n2)
                elif est is None:
                    raise PoolError(f"{label}: md needs estimate + se/CI or m1,sd1,n1,m2,sd2,n2")
                elif se is None:
                    if lo is not None and hi is not None:
                        se = _ci_to_se(lo, hi, level)
                    else:
                        raise PoolError(f"{label}: md needs se or a CI")
                y, v = est * sign, se ** 2
            else:
                if have_groups:
                    sp = math.sqrt(((n1 - 1) * sd1 ** 2 + (n2 - 1) * sd2 ** 2) / (n1 + n2 - 2))
                    d = (m1 - m2) / sp
                elif est is not None and n1 is not None and n2 is not None:
                    d = est  # reported Cohen d (or g; correction is near-idempotent)
                    notes.append(f"{label}: reported d taken as given and Hedges-corrected.")
                else:
                    raise PoolError(f"{label}: smd needs m1,sd1,n1,m2,sd2,n2 or estimate (d) + n1,n2")
                df = n1 + n2 - 2
                J = 1 - 3 / (4 * df - 1)          # Hedges 1981 small-sample correction
                g = J * d * sign
                y = g
                v = (n1 + n2) / (n1 * n2) + g ** 2 / (2 * (n1 + n2))
                est = g
                n = n1 + n2

        elif outcome == "generic":
            if est is None:
                raise PoolError(f"{label}: generic needs 'estimate'")
            if se is None:
                if lo is not None and hi is not None:
                    se = _ci_to_se(lo, hi, level)
                else:
                    raise PoolError(f"{label}: generic needs se or a CI")
            y, v = est * sign, se ** 2

        elif outcome == "logratio":
            if est is None or est <= 0:
                raise PoolError(f"{label}: logratio needs a positive 'estimate'")
            if se is None:
                if lo is not None and hi is not None:
                    se = _ci_to_se(lo, hi, level, math.log)
                else:
                    raise PoolError(f"{label}: logratio needs se (log scale) or a CI")
            y, v = math.log(est), se ** 2

        if v is None or v <= 0 or not math.isfinite(v):
            raise PoolError(f"{label}: variance is {v}; check inputs")
        studies.append(Study(label=label, study_id=sid, y=float(y), v=float(v), n=n,
                             est_nat=float(scale.back(y)) if scale.back else float(est),
                             extra={k: r.get(k, "") for k in r}))

    cohorts = [s.extra.get("cohort", "") for s in studies if s.extra.get("cohort")]
    dupc = sorted({c for c in cohorts if cohorts.count(c) > 1})
    if dupc:
        warn(f"several rows come from the same cohort ({', '.join(dupc)}; see studies.csv). Overlapping samples are not "
             "independent: keep one estimate per cohort.", warnings)
    ids = [s.study_id for s in studies]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        warn(f"study_id appears more than once: {', '.join(dup)}. Multiple effects from one study are not independent; "
             "pick one per study or justify (see SKILL.md 'When not to pool').", warnings)
    return studies, scale, notes


# --------------------------------------------------------------------------
# Models
# --------------------------------------------------------------------------

def reml_tau2(y: np.ndarray, v: np.ndarray, X: np.ndarray | None = None) -> float:
    """REML estimate of tau^2 (Viechtbauer 2005) by bounded 1-D optimisation."""
    k = len(y)
    if X is None:
        X = np.ones((k, 1))
    p = X.shape[1]
    if k <= p:
        return 0.0

    def negll(t2):
        w = 1 / (v + t2)
        W = np.diag(w)
        XtWX = X.T @ W @ X
        beta = np.linalg.solve(XtWX, X.T @ W @ y)
        res = y - X @ beta
        _, logdet = np.linalg.slogdet(XtWX)
        return 0.5 * (np.sum(np.log(v + t2)) + logdet + np.sum(w * res ** 2))

    upper = max(100 * np.var(y, ddof=1) if k > 1 else 1.0, 10 * np.max(v), 1e-6)
    res = optimize.minimize_scalar(negll, bounds=(0.0, upper), method="bounded",
                                   options={"xatol": 1e-10})
    t2 = float(res.x)
    # check the boundary at 0 explicitly (likelihood may be monotone)
    if negll(0.0) <= res.fun:
        t2 = 0.0
    return max(t2, 0.0)


def dl_tau2(y, v):
    w = 1 / v
    ybar = np.sum(w * y) / np.sum(w)
    Q = np.sum(w * (y - ybar) ** 2)
    df = len(y) - 1
    C = np.sum(w) - np.sum(w ** 2) / np.sum(w)
    return max(0.0, (Q - df) / C) if C > 0 else 0.0


def fit(y: np.ndarray, v: np.ndarray, method="REML", hksj=True, hksj_truncate=False,
        level=0.95) -> dict:
    """Intercept-only model. Returns a dict of results on the analysis scale."""
    k = len(y)
    w = 1 / v
    fe = np.sum(w * y) / np.sum(w)
    fe_var = 1 / np.sum(w)
    Q = float(np.sum(w * (y - fe) ** 2))
    df = k - 1
    Qp = float(stats.chi2.sf(Q, df)) if df > 0 else float("nan")

    if k < 2:
        tau2 = 0.0
    elif method == "DL":
        tau2 = dl_tau2(y, v)
    elif method == "FE":
        tau2 = 0.0
    else:
        tau2 = reml_tau2(y, v)

    # I^2 and H^2 from tau^2 and the 'typical' within-study variance s^2
    # (Higgins & Thompson 2002, as metafor does); identical to the Q-based
    # (Q-df)/Q for DL, and consistent with the REML tau^2 otherwise.
    if df > 0:
        s2 = df * np.sum(w) / (np.sum(w) ** 2 - np.sum(w ** 2))
        I2 = 100 * tau2 / (tau2 + s2) if method != "FE" else max(0.0, (Q - df) / Q) * 100 if Q > 0 else 0.0
        H2 = (tau2 + s2) / s2 if method != "FE" else Q / df
    else:
        I2, H2 = 0.0, float("nan")

    ws = 1 / (v + tau2)
    mu = float(np.sum(ws * y) / np.sum(ws))
    var = 1 / np.sum(ws)
    crit_type = "z"
    dfree = None
    use_hksj = hksj and k >= MIN_K_FULL and method != "FE"
    if use_hksj:
        q = float(np.sum(ws * (y - mu) ** 2) / (k - 1))
        if hksj_truncate:
            q = max(q, 1.0)
        var = q * var
        crit = stats.t.ppf(0.5 + level / 2, k - 1)
        crit_type, dfree = "t", k - 1
    else:
        crit = stats.norm.ppf(0.5 + level / 2)
    se = math.sqrt(var)
    ci = (mu - crit * se, mu + crit * se)
    if crit_type == "t":
        p = 2 * stats.t.sf(abs(mu / se), k - 1)
    else:
        p = 2 * stats.norm.sf(abs(mu / se))

    # Prediction interval (Higgins 2009; IntHout 2016): t with k-2 df
    if k >= MIN_K_FULL and method != "FE":
        tcrit = stats.t.ppf(0.5 + level / 2, k - 2)
        pi_se = math.sqrt(tau2 + var)
        pi = (mu - tcrit * pi_se, mu + tcrit * pi_se)
    else:
        pi = (float("nan"), float("nan"))

    weights = ws / np.sum(ws) * 100
    return {
        "k": k, "method": method, "hksj": use_hksj, "crit": crit_type, "df": dfree,
        "estimate": mu, "se": se, "ci_low": ci[0], "ci_high": ci[1], "p": float(p),
        "pi_low": pi[0], "pi_high": pi[1],
        "tau2": float(tau2), "tau": math.sqrt(tau2), "I2": float(I2), "H2": float(H2),
        "Q": Q, "Q_df": df, "Q_p": Qp,
        "fe_estimate": float(fe), "fe_se": math.sqrt(fe_var),
        "fe_ci_low": float(fe - stats.norm.ppf(0.5 + level / 2) * math.sqrt(fe_var)),
        "fe_ci_high": float(fe + stats.norm.ppf(0.5 + level / 2) * math.sqrt(fe_var)),
        "weights_pct": weights.tolist(),
        "fe_weights_pct": (w / np.sum(w) * 100).tolist(),
    }


def metareg(y, v, X, names, method="REML", kh=True, level=0.95) -> dict:
    k, p = X.shape
    tau2 = reml_tau2(y, v, X) if method == "REML" else 0.0
    if method == "DL":
        # DL for meta-regression (method-of-moments, Raudenbush 2009)
        w = 1 / v
        W = np.diag(w)
        P = W - W @ X @ np.linalg.solve(X.T @ W @ X, X.T @ W)
        Qe = float(y @ P @ y)
        tau2 = max(0.0, (Qe - (k - p)) / np.trace(P))
    # residual heterogeneity test uses the fixed-effect (1/v) weighted fit
    wf = 1 / v
    Wf = np.diag(wf)
    beta_f = np.linalg.solve(X.T @ Wf @ X, X.T @ Wf @ y)
    QE = float(np.sum(wf * (y - X @ beta_f) ** 2))
    w = 1 / (v + tau2)
    W = np.diag(w)
    XtWX = X.T @ W @ X
    cov = np.linalg.inv(XtWX)
    beta = cov @ X.T @ W @ y
    res = y - X @ beta
    Qe = float(np.sum(w * res ** 2))   # RE-weighted; drives the Knapp-Hartung factor
    if kh and k - p >= 2:
        q = Qe / (k - p)
        cov = cov * q
        crit = stats.t.ppf(0.5 + level / 2, k - p)
        pvals = [2 * stats.t.sf(abs(b / math.sqrt(cov[i, i])), k - p) for i, b in enumerate(beta)]
        test = "t"
    else:
        crit = stats.norm.ppf(0.5 + level / 2)
        pvals = [2 * stats.norm.sf(abs(b / math.sqrt(cov[i, i]))) for i, b in enumerate(beta)]
        test = "z"
    # omnibus test of moderators (all but intercept)
    idx = list(range(1, p))
    if idx:
        b = beta[idx]
        C = cov[np.ix_(idx, idx)]
        QM = float(b @ np.linalg.solve(C, b))
        if test == "t":
            F = QM / len(idx)
            QM_p = float(stats.f.sf(F, len(idx), k - p))
            omni = {"stat": F, "dist": f"F({len(idx)}, {k - p})", "p": QM_p}
        else:
            omni = {"stat": QM, "dist": f"chi2({len(idx)})", "p": float(stats.chi2.sf(QM, len(idx)))}
    else:
        omni = None
    tau2_null = reml_tau2(y, v) if method == "REML" else dl_tau2(y, v)
    R2 = max(0.0, (tau2_null - tau2) / tau2_null) * 100 if tau2_null > 0 else float("nan")
    coefs = []
    for i, nm in enumerate(names):
        se = math.sqrt(cov[i, i])
        coefs.append({"term": nm, "estimate": float(beta[i]), "se": se,
                      "ci_low": float(beta[i] - crit * se), "ci_high": float(beta[i] + crit * se),
                      "p": float(pvals[i])})
    return {"k": k, "p": p, "tau2": float(tau2), "tau2_null": float(tau2_null), "R2": float(R2),
            "QE": QE, "QE_df": k - p, "QE_p": float(stats.chi2.sf(QE, k - p)),
            "omnibus": omni, "test": test, "coefficients": coefs}


def egger(y, v, level=0.95) -> dict:
    """Egger regression test: weighted regression of y on se (Sterne & Egger 2005 form)."""
    se = np.sqrt(v)
    X = np.column_stack([np.ones_like(y), se])
    W = np.diag(1 / v)
    cov = np.linalg.inv(X.T @ W @ X)
    beta = cov @ X.T @ W @ y
    res = y - X @ beta
    k = len(y)
    s2 = float(np.sum((res ** 2) / v) / (k - 2))
    cov = cov * s2
    t = beta[1] / math.sqrt(cov[1, 1])
    p = 2 * stats.t.sf(abs(t), k - 2)
    return {"intercept_bias": float(beta[1]), "se": float(math.sqrt(cov[1, 1])),
            "t": float(t), "df": k - 2, "p": float(p)}


# --------------------------------------------------------------------------
# Plots
# --------------------------------------------------------------------------

def forest_plot(studies, res, scale, title, path_base, level):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    k = len(studies)
    crit = stats.norm.ppf(0.5 + level / 2)
    back = scale.back
    ys = np.array([s.y for s in studies])
    ses = np.sqrt([s.v for s in studies])
    lo, hi = back(ys - crit * ses), back(ys + crit * ses)
    est = back(ys)
    pooled = res is not None
    fig_h = 1.0 + 0.42 * (k + (3 if pooled else 1))
    fig, ax = plt.subplots(figsize=(10.5, fig_h))
    ypos = np.arange(k, 0, -1) + (2 if pooled else 0)
    weights = np.array(res["weights_pct"]) if pooled else np.full(k, 100 / k)
    sizes = 40 + 260 * weights / weights.max()
    ax.hlines(ypos, lo, hi, color="#1f3b57", lw=1.3)
    ax.scatter(est, ypos, s=sizes, marker="s", color="#1f3b57", zorder=3)
    labels = [s.label for s in studies]
    text_vals = [f"{e:.2f} [{l:.2f}, {h:.2f}]" for e, l, h in zip(est, lo, hi)]
    wtxt = [f"{w:.1f}%" for w in weights]
    if pooled:
        mu, cl, ch = back(res["estimate"]), back(res["ci_low"]), back(res["ci_high"])
        dy = 0.3
        ax.fill([cl, mu, ch, mu], [1.5, 1.5 + dy, 1.5, 1.5 - dy], color="#8a2b2b", zorder=4)
        model_name = ("FE" if res["method"] == "FE" else f"RE ({res['method']}" + (", HKSJ)" if res["hksj"] else ")"))
        labels.append(f"Pooled, {model_name}")
        text_vals.append(f"{mu:.2f} [{cl:.2f}, {ch:.2f}]")
        wtxt.append("100%")
        ypos = np.append(ypos, 1.5)
        if math.isfinite(res["pi_low"]):
            pl, ph = back(res["pi_low"]), back(res["pi_high"])
            ax.hlines(0.6, pl, ph, color="#8a2b2b", lw=3, alpha=0.55)
            labels.append("95% prediction interval")
            text_vals.append(f"[{pl:.2f}, {ph:.2f}]")
            wtxt.append("")
            ypos = np.append(ypos, 0.6)
        ax.axvline(mu, color="#8a2b2b", lw=0.8, ls="--")
    null = {"Fisher z": 0.0, "logit": None, "log": 1.0, "natural": 0.0}.get(scale.name)
    if scale.natural in ("AUC",):
        null = 0.5
    if scale.natural in ("Proportion", "Mean"):
        null = None
    if null is not None:
        ax.axvline(null, color="grey", lw=0.8)
    if scale.log_axis:
        ax.set_xscale("log")
    ax.set_yticks(ypos)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_ylim(0, ypos.max() + 1)
    ax.set_xlabel(scale.natural)
    ax.set_title(title, fontsize=11, loc="left")
    xmin, xmax = ax.get_xlim()
    for yy, tv, wt in zip(ypos, text_vals, wtxt):
        ax.text(1.02, yy, tv, transform=ax.get_yaxis_transform(), fontsize=8.5, va="center")
        ax.text(1.40, yy, wt, transform=ax.get_yaxis_transform(), fontsize=8.5, va="center")
    ax.text(1.02, ypos.max() + 0.7, f"{scale.natural} [{int(level*100)}% CI]", transform=ax.get_yaxis_transform(), fontsize=8.5, weight="bold")
    ax.text(1.40, ypos.max() + 0.7, "Weight", transform=ax.get_yaxis_transform(), fontsize=8.5, weight="bold")
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    fig.subplots_adjust(left=0.26, right=0.68, top=0.9, bottom=0.12)
    fig.savefig(path_base + ".svg", metadata={"Date": None})
    fig.savefig(path_base + ".png", dpi=150)
    plt.close(fig)


def funnel_plot(studies, res, scale, title, path_base, level):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ys = np.array([s.y for s in studies])
    ses = np.sqrt([s.v for s in studies])
    crit = stats.norm.ppf(0.5 + level / 2)
    mu = res["estimate"]
    fig, ax = plt.subplots(figsize=(6.5, 5))
    top = ses.max() * 1.1
    ss = np.linspace(0, top, 50)
    ax.plot(mu - crit * ss, ss, color="grey", lw=0.8, ls="--")
    ax.plot(mu + crit * ss, ss, color="grey", lw=0.8, ls="--")
    ax.axvline(mu, color="#8a2b2b", lw=0.8)
    ax.scatter(ys, ses, color="#1f3b57", zorder=3)
    ax.invert_yaxis()
    ax.set_xlabel(f"Effect ({scale.name} scale)")
    ax.set_ylabel("Standard error")
    ax.set_title(title, fontsize=11, loc="left")
    if scale.back is not None and scale.name != "natural":
        ticks = ax.get_xticks()
        ax.set_xticks(ticks)
        ax.set_xticklabels([f"{t:.2g}\n({float(scale.back(t)):.2f})" for t in ticks], fontsize=8)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    fig.tight_layout()
    fig.savefig(path_base + ".svg", metadata={"Date": None})
    fig.savefig(path_base + ".png", dpi=150)
    plt.close(fig)


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------

def fmt(x, nd=3):
    if x is None or (isinstance(x, float) and not math.isfinite(x)):
        return "NA"
    return f"{x:.{nd}f}"


def fmtp(p):
    if p is None or not math.isfinite(p):
        return "NA"
    return "<0.001" if p < 0.001 else f"{p:.3f}"


def methods_paragraph(outcome, res, args, scale, k, extras) -> str:
    tr = {
        "correlation": "Correlation coefficients were converted to Fisher z (variance 1/(n-3)), pooled, and back-transformed to r",
        "spearman": "Spearman coefficients were converted to Fisher z with the Bonett and Wright (2000) variance (1 + rho^2/2)/(n-3), pooled, and back-transformed",
        "auc": ("AUCs were pooled on the logit scale (delta-method variances) and back-transformed" if args.auc_scale == "logit"
                else "AUCs were pooled on their natural scale; standard errors were taken from reported confidence intervals or derived with the Hanley and McNeil (1982) method"),
        "proportion": {"logit": "Proportions were pooled on the logit scale and back-transformed",
                       "ftt": "Proportions were stabilised with the Freeman-Tukey double arcsine transform and back-transformed with the harmonic-mean inverse (Miller 1978; Barker 2021)",
                       "none": "Proportions were pooled on the raw scale"}[args.transform],
        "mean": "Means were pooled on their natural scale",
        "md": "Mean differences were pooled on their natural scale",
        "smd": "Standardised mean differences were expressed as Hedges g with the small-sample correction",
        "generic": "Estimates were pooled with their reported standard errors",
        "logratio": "Ratio measures were pooled on the log scale and back-transformed",
    }[outcome]
    if res["method"] == "FE" or k < MIN_K_FULL:
        model = (f"Because only {k} studies contributed, a fixed-effect (inverse-variance) estimate is shown for "
                 "description only and no between-study variance was estimated")
    else:
        model = (f"A random-effects model was fitted with between-study variance (tau^2) estimated by "
                 f"{'restricted maximum likelihood (REML; Veroniki 2016; Langan 2019)' if res['method']=='REML' else 'the DerSimonian-Laird method'}")
        if res["hksj"]:
            model += ", and confidence intervals used the Hartung-Knapp-Sidik-Jonkman adjustment (IntHout 2014)"
    text = f"{tr}. {model}."
    if not (res["method"] == "FE" or k < MIN_K_FULL):
        text += " Heterogeneity was summarised with tau^2, I^2 and a 95% prediction interval (Higgins 2009; IntHout 2016)."
    if extras.get("loo"):
        text += " Leave-one-out analyses assessed the influence of single studies."
    if extras.get("subgroup"):
        text += f" Subgroups by {extras['subgroup']} were compared with a between-groups Q test (separate tau^2 per subgroup)."
    if extras.get("metareg"):
        text += f" A mixed-effects meta-regression on {', '.join(extras['metareg'])} used REML with the Knapp-Hartung test."
    if extras.get("egger") == "done":
        text += " Small-study effects were assessed with Egger's regression test and a funnel plot."
    text += (" Analyses were run in Python (numpy/scipy) with a script written with AI assistance "
             "(Claude); all outputs were checked by the reviewers, who made the final analytic decisions.")
    return text


def write_outputs(outdir, name, outcome, studies, res, scale, args, notes, warnings, extras):
    os.makedirs(outdir, exist_ok=True)
    back = scale.back
    level = args.level
    crit = stats.norm.ppf(0.5 + level / 2)
    k = len(studies)

    # per_study.csv
    with open(os.path.join(outdir, "per_study.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["study_id", "label", "n", "estimate_natural", "ci_low_natural", "ci_high_natural",
                    "y_analysis", "se_analysis", "weight_re_pct", "weight_fe_pct"])
        for i, s in enumerate(studies):
            se = math.sqrt(s.v)
            w.writerow([s.study_id, s.label, "" if s.n is None else f"{s.n:g}",
                        fmt(float(back(s.y)), 4), fmt(float(back(s.y - crit * se)), 4), fmt(float(back(s.y + crit * se)), 4),
                        fmt(s.y, 5), fmt(se, 5),
                        fmt(res["weights_pct"][i], 2) if res else "", fmt(res["fe_weights_pct"][i], 2) if res else ""])

    summary = {
        "name": name, "outcome_type": outcome, "k": k, "scale": scale.name, "natural_scale": scale.natural,
        "pooled": res is not None,
        "studies": [{"study_id": s.study_id, "label": s.label, "n": s.n, "y": s.y, "v": s.v,
                     "estimate_natural": float(back(s.y))} for s in studies],
        "notes": notes, "warnings": warnings, "args": {k_: v_ for k_, v_ in vars(args).items() if k_ != "row"},
        "version": VERSION,
    }
    if res:
        summary["model"] = dict(res)
        summary["model_natural"] = {
            "estimate": float(back(res["estimate"])), "ci_low": float(back(res["ci_low"])), "ci_high": float(back(res["ci_high"])),
            "pi_low": float(back(res["pi_low"])) if math.isfinite(res["pi_low"]) else None,
            "pi_high": float(back(res["pi_high"])) if math.isfinite(res["pi_high"]) else None,
            "fe_estimate": float(back(res["fe_estimate"])), "fe_ci_low": float(back(res["fe_ci_low"])),
            "fe_ci_high": float(back(res["fe_ci_high"])),
        }
    summary.update({k_: v_ for k_, v_ in extras.items() if k_ not in ("loo", "subgroup", "metareg", "egger")})
    for key in ("loo_results", "subgroup_results", "metareg_results", "egger_results"):
        if key in extras:
            summary[key] = extras[key]
    with open(os.path.join(outdir, "results.json"), "w") as fh:
        json.dump(summary, fh, indent=2, default=lambda o: None if (isinstance(o, float) and not math.isfinite(o)) else str(o))

    # summary.md
    L = []
    L.append(f"# {name}: pooled {OUTCOME_TYPES[outcome].split(' (')[0]}\n")
    L.append(f"- Outcome type: `{outcome}`; analysis scale: {scale.name}; reported on: {scale.natural}")
    L.append(f"- Studies: k = {k}")
    if args.where:
        L.append(f"- Filter: {'; '.join(args.where)}")
    if res is None:
        L.append("\n**Not pooled** (k = 1). The single study is listed below; report it narratively.\n")
    else:
        mn = summary["model_natural"]
        L.append("")
        if res["method"] == "FE" or k < MIN_K_FULL:
            L.append(f"**Pooled {scale.natural} (fixed-effect, k = {k}; descriptive only): {fmt(mn['estimate'])} "
                     f"[{int(level*100)}% CI {fmt(mn['ci_low'])}, {fmt(mn['ci_high'])}]**")
            L.append(f"\nWARNING: with k = {k} there is no usable estimate of between-study variance, so this is a "
                     "weighted average of two studies, not a random-effects summary. Prefer reporting both studies side by side.")
        else:
            model_name = f"random-effects, {res['method']}" + (", HKSJ" if res["hksj"] else "")
            L.append(f"**Pooled {scale.natural} ({model_name}): {fmt(mn['estimate'])} "
                     f"[{int(level*100)}% CI {fmt(mn['ci_low'])}, {fmt(mn['ci_high'])}]**, p = {fmtp(res['p'])}")
            if mn["pi_low"] is not None:
                L.append(f"- 95% prediction interval: {fmt(mn['pi_low'])} to {fmt(mn['pi_high'])}")
            L.append(f"- Heterogeneity: tau^2 = {fmt(res['tau2'], 4)} (tau = {fmt(res['tau'])}), I^2 = {fmt(res['I2'], 1)}%, "
                     f"H^2 = {fmt(res['H2'], 2)}, Q = {fmt(res['Q'], 2)} on {res['Q_df']} df, p = {fmtp(res['Q_p'])}")
            L.append(f"- Fixed-effect comparison: {fmt(mn['fe_estimate'])} [{fmt(mn['fe_ci_low'])}, {fmt(mn['fe_ci_high'])}]")
            L.append(f"- Analysis-scale pooled value: {fmt(res['estimate'], 4)} (SE {fmt(res['se'], 4)}), "
                     f"{res['crit']}-based CI" + (f" with {res['df']} df" if res['df'] else ""))
    L.append("\n## Per-study estimates\n")
    L.append(f"| Study | n | {scale.natural} [{int(level*100)}% CI] | Weight |")
    L.append("|---|---|---|---|")
    for i, s in enumerate(studies):
        se = math.sqrt(s.v)
        wt = fmt(res["weights_pct"][i], 1) + "%" if res else ""
        L.append(f"| {s.label} | {'' if s.n is None else f'{s.n:g}'} | {fmt(float(back(s.y)))} "
                 f"[{fmt(float(back(s.y - crit*se)))}, {fmt(float(back(s.y + crit*se)))}] | {wt} |")

    if "loo_results" in extras:
        L.append("\n## Leave-one-out\n")
        L.append(f"| Omitted | Pooled {scale.natural} [CI] | tau^2 | I^2 |")
        L.append("|---|---|---|---|")
        for r in extras["loo_results"]:
            L.append(f"| {r['omitted']} | {fmt(r['estimate'])} [{fmt(r['ci_low'])}, {fmt(r['ci_high'])}] | {fmt(r['tau2'], 4)} | {fmt(r['I2'], 1)}% |")
    if "subgroup_results" in extras:
        sg = extras["subgroup_results"]
        L.append(f"\n## Subgroups by `{sg['column']}`\n")
        L.append(f"| Subgroup | k | Pooled {scale.natural} [CI] | tau^2 | I^2 |")
        L.append("|---|---|---|---|---|")
        for g in sg["groups"]:
            L.append(f"| {g['group']} | {g['k']} | {fmt(g['estimate'])} [{fmt(g['ci_low'])}, {fmt(g['ci_high'])}] | {fmt(g['tau2'], 4)} | {fmt(g['I2'], 1)}% |")
        L.append(f"\nBetween-groups Q = {fmt(sg['Q_between'], 2)} on {sg['df']} df, p = {fmtp(sg['p'])} "
                 "(separate tau^2 per subgroup). With few studies per subgroup this test has little power and subgroup "
                 "differences are observational, not causal.")
    if "metareg_results" in extras:
        mr = extras["metareg_results"]
        L.append("\n## Meta-regression (mixed-effects, REML, Knapp-Hartung)\n")
        L.append("| Term | Estimate (analysis scale) | SE | CI | p |")
        L.append("|---|---|---|---|---|")
        for c in mr["coefficients"]:
            L.append(f"| {c['term']} | {fmt(c['estimate'], 4)} | {fmt(c['se'], 4)} | [{fmt(c['ci_low'], 4)}, {fmt(c['ci_high'], 4)}] | {fmtp(c['p'])} |")
        if mr["omnibus"]:
            L.append(f"\nOmnibus test of moderators: {mr['omnibus']['dist']} = {fmt(mr['omnibus']['stat'], 2)}, p = {fmtp(mr['omnibus']['p'])}. "
                     f"Residual tau^2 = {fmt(mr['tau2'], 4)} (vs {fmt(mr['tau2_null'], 4)} without moderators; R^2 analogue = {fmt(mr['R2'], 1)}%). "
                     f"Residual heterogeneity QE = {fmt(mr['QE'], 2)} on {mr['QE_df']} df, p = {fmtp(mr['QE_p'])}.")
    if "egger_results" in extras:
        eg = extras["egger_results"]
        L.append("\n## Small-study effects\n")
        L.append(f"Egger's test: bias coefficient = {fmt(eg['intercept_bias'], 3)} (SE {fmt(eg['se'], 3)}), t = {fmt(eg['t'], 2)} on {eg['df']} df, p = {fmtp(eg['p'])}. "
                 "See funnel.svg. Asymmetry can reflect heterogeneity, reporting practices or chance as well as publication bias (Sterne 2011).")
    if extras.get("egger") and extras["egger"] != "done":
        L.append("\n## Small-study effects\n")
        L.append(extras["egger"])

    if notes:
        L.append("\n## Notes on inputs\n")
        L.extend(f"- {n}" for n in notes)
    if warnings:
        L.append("\n## Warnings\n")
        L.extend(f"- {w}" for w in warnings)
    L.append("\n## Methods paragraph (template; edit before use)\n")
    if res:
        L.append(methods_paragraph(outcome, res, args, scale, k, extras))
    else:
        L.append("Only one study reported this outcome, so it was described narratively rather than pooled.")
    L.append("\nAI assistance: this analysis was produced with a script written and run by an AI assistant (Claude) under "
             "reviewer direction. State this in the Methods. The numbers are advisory; the reviewer checks and decides.")
    L.append("\nFiles: results.json, per_study.csv, forest.svg/png" + (", funnel.svg/png" if "egger_results" in extras else "") + ".")
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def build_parser():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("csv", nargs="?", help="effects.csv from the data-extraction skill (omit when using --row)")
    p.add_argument("--row", action="append", default=[], help="ad-hoc study as key=value pairs, e.g. 'label=Smith 2019,estimate=0.42,n=110' (repeatable)")
    p.add_argument("--outcome", choices=list(OUTCOME_TYPES) + sorted(TYPE_ALIASES), metavar="TYPE",
                   help="outcome type to pool (required if the CSV has more than one): " + ", ".join(OUTCOME_TYPES)
                   + "; aliases: " + ", ".join(f"{a}={b}" for a, b in TYPE_ALIASES.items()))
    p.add_argument("--name", required=True, help="analysis name; outputs go to <out>/<name>/")
    p.add_argument("--out", default="analysis/effects", help="output root (default analysis/effects)")
    p.add_argument("--studies", metavar="CSV", help="studies.csv from data-extraction for labels (citation) and cohorts; auto-detected beside the effects CSV")
    p.add_argument("--where", action="append", default=[], help="filter rows: col=value (exact) or col~regex (repeatable)")
    p.add_argument("--method", choices=["REML", "DL", "FE"], default="REML", help="tau^2 estimator (default REML)")
    p.add_argument("--no-hksj", action="store_true", help="use normal (z) CIs instead of Hartung-Knapp-Sidik-Jonkman")
    p.add_argument("--hksj-truncate", action="store_true", help="modified HKSJ: never narrower than the z-based CI")
    p.add_argument("--level", type=float, default=0.95, help="confidence level (default 0.95)")
    p.add_argument("--transform", choices=["logit", "ftt", "none"], default="logit", help="proportion transform (default logit)")
    p.add_argument("--auc-scale", choices=["natural", "logit"], default="natural", help="AUC analysis scale (default natural)")
    p.add_argument("--mix-correlations", action="store_true", help="allow Pearson and Spearman rows to be pooled together (not recommended)")
    p.add_argument("--loo", action="store_true", help="leave-one-out sensitivity analysis")
    p.add_argument("--subgroup", metavar="COL", help="subgroup analysis by a categorical column")
    p.add_argument("--moderators", metavar="COLS", help="comma-separated covariates for meta-regression")
    p.add_argument("--force-metareg", action="store_true", help="run meta-regression even with < 10 studies per covariate")
    p.add_argument("--egger", action="store_true", help="Egger's test + funnel plot (only when k >= 10 and not a proportion)")
    p.add_argument("--title", help="forest plot title (default: name)")
    p.add_argument("--no-plots", action="store_true", help="skip SVG/PNG output")
    return p


def run_subgroups(studies, col, args, warnings, back):
    groups: dict[str, list[Study]] = {}
    for s in studies:
        g = s.extra.get(col, "") or "(missing)"
        groups.setdefault(g, []).append(s)
    if len(groups) < 2:
        warn(f"--subgroup {col}: only one level present; skipping", warnings)
        return None
    out = []
    for g, ss in groups.items():
        y = np.array([s.y for s in ss]); v = np.array([s.v for s in ss])
        if len(ss) == 1:
            out.append({"group": g, "k": 1, "estimate": float(back(y[0])), "ci_low": float(back(y[0] - 1.96 * math.sqrt(v[0]))),
                        "ci_high": float(back(y[0] + 1.96 * math.sqrt(v[0]))), "tau2": float("nan"), "I2": float("nan"),
                        "y": float(y[0]), "var": float(v[0])})
            continue
        r = fit(y, v, method=args.method if len(ss) >= MIN_K_FULL else "FE", hksj=not args.no_hksj,
                hksj_truncate=args.hksj_truncate, level=args.level)
        out.append({"group": g, "k": len(ss), "estimate": float(back(r["estimate"])), "ci_low": float(back(r["ci_low"])),
                    "ci_high": float(back(r["ci_high"])), "tau2": r["tau2"], "I2": r["I2"], "y": r["estimate"], "var": r["se"] ** 2})
    # between-groups Q (Borenstein 2009 ch. 19, separate tau^2)
    wg = np.array([1 / g["var"] for g in out]); yg = np.array([g["y"] for g in out])
    ybar = np.sum(wg * yg) / np.sum(wg)
    Qb = float(np.sum(wg * (yg - ybar) ** 2)); df = len(out) - 1
    small = [g["group"] for g in out if g["k"] < MIN_K_FULL]
    if small:
        warn(f"subgroups with fewer than {MIN_K_FULL} studies ({', '.join(small)}): their pooled values are descriptive only", warnings)
    return {"column": col, "groups": out, "Q_between": Qb, "df": df, "p": float(stats.chi2.sf(Qb, df))}


def run_metareg(studies, cols, args, warnings):
    k = len(studies)
    need = MIN_K_PER_COVARIATE * len(cols)
    if k < need and not args.force_metareg:
        msg = (f"meta-regression refused: {k} studies for {len(cols)} covariate(s); rule adopted is >= {MIN_K_PER_COVARIATE} "
               "studies per covariate (Cochrane Handbook 10.11.5.1), because with fewer the regression over-fits and "
               "false-positive moderator effects are common. Use --force-metareg to override (and say so in the write-up).")
        warn(msg, warnings)
        return None
    if k < need:
        warn(f"meta-regression forced with {k} studies for {len(cols)} covariate(s) (< {MIN_K_PER_COVARIATE} per covariate): "
             "treat as exploratory and say so in the write-up", warnings)
    X_cols = [np.ones(k)]; names = ["intercept"]
    for c in cols:
        vals = [s.extra.get(c, "") for s in studies]
        try:
            num = np.array([float(x) for x in vals])
            X_cols.append(num); names.append(c)
        except ValueError:
            levels = sorted(set(vals))
            if len(levels) < 2:
                raise PoolError(f"moderator {c} has a single level")
            for lv in levels[1:]:
                X_cols.append(np.array([1.0 if x == lv else 0.0 for x in vals])); names.append(f"{c}={lv} (vs {levels[0]})")
    X = np.column_stack(X_cols)
    if np.linalg.matrix_rank(X) < X.shape[1]:
        raise PoolError("moderator design matrix is rank-deficient (collinear covariates)")
    y = np.array([s.y for s in studies]); v = np.array([s.v for s in studies])
    return metareg(y, v, X, names, method="REML" if args.method != "DL" else "DL", kh=not args.no_hksj, level=args.level)


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    warnings: list[str] = []
    try:
        if args.csv:
            rows = read_rows(args.csv)
        elif args.row:
            rows = [parse_adhoc_row(r) for r in args.row]
        else:
            raise PoolError("give a CSV path or at least one --row")
        if args.row and args.csv:
            rows += [parse_adhoc_row(r) for r in args.row]
        rows = normalise_rows(rows, load_studies_table(args.studies, args.csv), warnings)
        rows = apply_where(rows, args.where)
        if not rows:
            raise PoolError("no rows left after --where filters")
        types = sorted({r["outcome_type"] for r in rows if r["outcome_type"]})
        outcome = TYPE_ALIASES.get(args.outcome, args.outcome) if args.outcome else None
        if outcome is None and args.mix_correlations:
            outcome = "correlation"
        if outcome is None:
            if len(types) == 1:
                outcome = types[0]
            elif not types:
                raise PoolError("rows have no outcome_type column; pass --outcome")
            elif set(types) == {"correlation", "spearman"}:
                raise PoolError("rows hold both Pearson and Spearman correlations; they estimate different quantities. "
                                "Pool them separately (--outcome correlation, then --outcome spearman) or pass --mix-correlations and justify it.")
            else:
                raise PoolError(f"CSV holds several outcome types ({', '.join(types)}); pass --outcome")
        if types:
            if outcome in ("correlation", "spearman") and args.mix_correlations:
                rows = [r for r in rows if r["outcome_type"] in ("correlation", "spearman")]
                if len({r["outcome_type"] for r in rows}) > 1:
                    warn("Pearson and Spearman correlations pooled together (--mix-correlations); each row keeps its own variance formula", warnings)
            else:
                other = [r for r in rows if r["outcome_type"] and r["outcome_type"] != outcome]
                rows = [r for r in rows if (r["outcome_type"] or outcome) == outcome]
                if outcome in ("correlation", "spearman"):
                    sib = "spearman" if outcome == "correlation" else "correlation"
                    left = [r["label"] for r in other if r["outcome_type"] == sib]
                    if left:
                        warn(f"{len(left)} {sib} row(s) set aside ({', '.join(left)}); pool them separately with --outcome {sib} "
                             "or merge with --mix-correlations", warnings)
        if not rows:
            raise PoolError(f"no rows with outcome_type={outcome}")
        if "instrument" in rows[0] and len({r.get("instrument") for r in rows}) > 1:
            warn(f"rows use {len({r.get('instrument') for r in rows})} different instruments ({', '.join(sorted({r.get('instrument','') for r in rows}))}). "
                 "Pooling across instruments answers a different question (\"do questionnaires of this kind correlate with X\"); say so, or filter with --where instrument=...", warnings)
        if "comparator" in rows[0] and len({r.get("comparator") for r in rows}) > 1:
            warn(f"rows use different comparators/reference standards ({', '.join(sorted({r.get('comparator','') for r in rows}))}). "
                 "Consider --where comparator=... or --subgroup comparator.", warnings)

        studies, scale, notes = build_studies(rows, outcome, args.level, args, warnings)
        k = len(studies)
        outdir = os.path.join(args.out, args.name)
        extras: dict = {}
        res = None
        y = np.array([s.y for s in studies]); v = np.array([s.v for s in studies])

        if k == 1:
            warn("k = 1: nothing to pool; writing a single-study summary", warnings)
        elif k == 2:
            warn("k = 2: reporting a fixed-effect average for description only; between-study variance cannot be estimated. "
                 "Prefer presenting both studies side by side.", warnings)
            res = fit(y, v, method="FE", hksj=False, level=args.level)
        else:
            res = fit(y, v, method=args.method, hksj=not args.no_hksj, hksj_truncate=args.hksj_truncate, level=args.level)
            if res["tau2"] == 0 and res["method"] != "FE":
                notes.append("tau^2 estimated at 0; the random-effects and fixed-effect estimates coincide (HKSJ CI may still differ).")
            if k < 5:
                warn(f"k = {k}: tau^2 and I^2 are very imprecise with so few studies; the prediction interval is wide by design. "
                     "Report the HKSJ CI and the individual studies, not just the pooled value.", warnings)

        if args.loo and k >= MIN_K_FULL:
            loo = []
            for i, s in enumerate(studies):
                mask = np.arange(k) != i
                r = fit(y[mask], v[mask], method=args.method if k - 1 >= MIN_K_FULL else "FE",
                        hksj=not args.no_hksj, hksj_truncate=args.hksj_truncate, level=args.level)
                loo.append({"omitted": s.label, "estimate": float(scale.back(r["estimate"])), "ci_low": float(scale.back(r["ci_low"])),
                            "ci_high": float(scale.back(r["ci_high"])), "tau2": r["tau2"], "I2": r["I2"]})
            extras["loo"] = True; extras["loo_results"] = loo
            os.makedirs(outdir, exist_ok=True)
            with open(os.path.join(outdir, "loo.csv"), "w", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=list(loo[0].keys())); w.writeheader(); w.writerows(loo)
        elif args.loo:
            warn("--loo needs at least 3 studies; skipped", warnings)

        if args.subgroup and k >= 2:
            sg = run_subgroups(studies, args.subgroup, args, warnings, scale.back)
            if sg:
                extras["subgroup"] = args.subgroup; extras["subgroup_results"] = sg
                os.makedirs(outdir, exist_ok=True)
                with open(os.path.join(outdir, "subgroups.csv"), "w", newline="") as fh:
                    w = csv.DictWriter(fh, fieldnames=["group", "k", "estimate", "ci_low", "ci_high", "tau2", "I2"], extrasaction="ignore")
                    w.writeheader(); w.writerows(sg["groups"])

        if args.moderators:
            cols = [c.strip() for c in args.moderators.split(",") if c.strip()]
            mr = run_metareg(studies, cols, args, warnings)
            if mr:
                extras["metareg"] = cols; extras["metareg_results"] = mr
                os.makedirs(outdir, exist_ok=True)
                with open(os.path.join(outdir, "metareg.csv"), "w", newline="") as fh:
                    w = csv.DictWriter(fh, fieldnames=["term", "estimate", "se", "ci_low", "ci_high", "p"]); w.writeheader(); w.writerows(mr["coefficients"])

        if args.egger:
            if outcome == "proportion":
                extras["egger"] = ("Egger's test not run: for proportions the estimate and its SE are mathematically linked, so funnel "
                                   "asymmetry tests give false positives (Hunter 2014). Report a funnel plot only descriptively, or no test.")
                warn(extras["egger"], warnings)
            elif k < MIN_K_EGGER:
                extras["egger"] = (f"Egger's test not run: k = {k} < {MIN_K_EGGER}. With fewer than 10 studies funnel-plot tests have too little "
                                   "power to distinguish chance from asymmetry (Sterne 2011).")
                warn(extras["egger"], warnings)
            else:
                extras["egger"] = "done"; extras["egger_results"] = egger(y, v, args.level)
                if res and res["I2"] > 75:
                    extras["egger_results"]["caveat"] = "I^2 > 75%: asymmetry may reflect heterogeneity rather than publication bias"
                if not args.no_plots:
                    os.makedirs(outdir, exist_ok=True)
                    funnel_plot(studies, res, scale, args.title or args.name, os.path.join(outdir, "funnel"), args.level)

        write_outputs(outdir, args.name, outcome, studies, res, scale, args, notes, warnings, extras)
        if not args.no_plots:
            forest_plot(studies, res, scale, args.title or args.name, os.path.join(outdir, "forest"), args.level)

        # console summary
        if res:
            mn = scale.back
            print(f"{args.name}: k={k} {OUTCOME_TYPES[outcome].split(' (')[0]} pooled ({res['method']}{', HKSJ' if res['hksj'] else ''}) = "
                  f"{float(mn(res['estimate'])):.3f} [{float(mn(res['ci_low'])):.3f}, {float(mn(res['ci_high'])):.3f}]"
                  + (f"; PI [{float(mn(res['pi_low'])):.3f}, {float(mn(res['pi_high'])):.3f}]" if math.isfinite(res["pi_low"]) else "")
                  + f"; tau^2={res['tau2']:.4f}, I^2={res['I2']:.1f}%")
        else:
            print(f"{args.name}: k=1, not pooled")
        print(f"wrote {outdir}/")
        return 0
    except PoolError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
