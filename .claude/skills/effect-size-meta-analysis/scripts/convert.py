#!/usr/bin/env python3
"""Turn what papers actually report into (estimate, SE) pairs for pool.py.

Subcommands (run `convert.py <sub> --help` for arguments):
  ci-to-se       CI -> SE on the normal, log, logit or Fisher-z scale
  auc-se         AUC + n_pos + n_neg -> SE (Hanley & McNeil 1982)
  spearman-var   Spearman rho + n -> Fisher-z variance (Bonett & Wright 2000)
  t-to-d         t statistic + group sizes -> Cohen d and Hedges g
  f-to-d         one-df F statistic + group sizes -> d and g (sign must be supplied)
  p-to-d         two-sided p + group sizes -> d and g (sign must be supplied)
  means-to-smd   m1 sd1 n1 m2 sd2 n2 -> Hedges g with variance
  d-to-r / r-to-d  convert between d and point-biserial r (Borenstein 2009)
  or-from-2x2    a b c d -> OR, log OR, SE, CI
  rr-from-2x2    a b c d -> RR, log RR, SE, CI
  se-from-sd     SD + n -> SE of a mean
  iqr-to-sd      IQR (and optionally median/range) -> approximate SD (Wan 2014)

Visual-acuity unit conversions (Snellen <-> logMAR, letters) are NOT done
here; see the data-extraction skill.  Output is key=value lines, or JSON
with --json.
"""
from __future__ import annotations

import argparse
import json
import math
import sys

try:
    from scipy import stats
except ImportError:  # python3 -I hides the user site; re-add that one trusted dir
    import site
    sys.path.append(site.getusersitepackages())
    try:
        from scipy import stats
    except ImportError:
        sys.exit("scipy is required: python3 -m pip install --user --break-system-packages scipy")


def zcrit(level: float) -> float:
    return stats.norm.ppf(0.5 + level / 2)


def hedges(d: float, n1: float, n2: float) -> dict:
    df = n1 + n2 - 2
    J = 1 - 3 / (4 * df - 1)
    g = J * d
    var_d = (n1 + n2) / (n1 * n2) + d ** 2 / (2 * (n1 + n2))
    var_g = (n1 + n2) / (n1 * n2) + g ** 2 / (2 * (n1 + n2))
    return {"d": d, "var_d": var_d, "se_d": math.sqrt(var_d), "J": J, "g": g, "var_g": var_g,
            "se_g": math.sqrt(var_g), "n1": n1, "n2": n2}


def cmd_ci_to_se(a):
    scale = a.scale
    f = {"normal": lambda x: x, "log": math.log, "logit": lambda p: math.log(p / (1 - p)),
         "fisherz": math.atanh}[scale]
    z = zcrit(a.level)
    se = (f(a.high) - f(a.low)) / (2 * z)
    out = {"scale": scale, "se": se}
    if a.estimate is not None:
        out["estimate_on_scale"] = f(a.estimate)
        # asymmetry check: how far the point estimate sits from the CI midpoint
        mid = (f(a.high) + f(a.low)) / 2
        out["midpoint_offset_in_se"] = (f(a.estimate) - mid) / se if se > 0 else float("nan")
        if abs(out["midpoint_offset_in_se"]) > 0.25:
            out["warning"] = ("point estimate is not at the CI midpoint on this scale; the CI may have been computed on "
                              "another scale or by a different method (bootstrap, exact). Check the paper.")
    return out


def cmd_auc_se(a):
    A, n1, n2 = a.auc, a.n_pos, a.n_neg
    q1 = A / (2 - A)
    q2 = 2 * A ** 2 / (1 + A)
    var = (A * (1 - A) + (n1 - 1) * (q1 - A ** 2) + (n2 - 1) * (q2 - A ** 2)) / (n1 * n2)
    se = math.sqrt(var)
    z = zcrit(a.level)
    return {"auc": A, "se": se, "ci_low": max(0.0, A - z * se), "ci_high": min(1.0, A + z * se),
            "method": "Hanley & McNeil 1982 (assumes the binormal/exponential approximation; usually close to DeLong)"}


def cmd_spearman_var(a):
    rho, n = a.rho, a.n
    z = math.atanh(rho)
    var = (1 + rho ** 2 / 2) / (n - 3)
    return {"rho": rho, "fisher_z": z, "var_z": var, "se_z": math.sqrt(var),
            "note": "Bonett & Wright 2000; compare Pearson var 1/(n-3) = %.5f" % (1 / (n - 3))}


def cmd_t_to_d(a):
    d = a.t * math.sqrt((a.n1 + a.n2) / (a.n1 * a.n2))
    return hedges(d, a.n1, a.n2)


def cmd_f_to_d(a):
    if a.F < 0:
        sys.exit("F must be non-negative")
    d = math.sqrt(a.F) * math.sqrt((a.n1 + a.n2) / (a.n1 * a.n2)) * (1 if a.sign >= 0 else -1)
    out = hedges(d, a.n1, a.n2)
    out["note"] = "valid only for a one-df F (two groups); sign supplied by --sign"
    return out


def cmd_p_to_d(a):
    df = a.n1 + a.n2 - 2
    t = stats.t.ppf(1 - a.p / 2, df) * (1 if a.sign >= 0 else -1)
    out = hedges(t * math.sqrt((a.n1 + a.n2) / (a.n1 * a.n2)), a.n1, a.n2)
    out["t_recovered"] = t
    out["note"] = "from an exact two-sided p; a p reported as '<0.05' gives only a bound"
    return out


def cmd_means_to_smd(a):
    sp = math.sqrt(((a.n1 - 1) * a.sd1 ** 2 + (a.n2 - 1) * a.sd2 ** 2) / (a.n1 + a.n2 - 2))
    d = (a.m1 - a.m2) / sp
    out = hedges(d, a.n1, a.n2)
    out["pooled_sd"] = sp
    out["md"] = a.m1 - a.m2
    out["se_md"] = math.sqrt(a.sd1 ** 2 / a.n1 + a.sd2 ** 2 / a.n2)
    return out


def cmd_d_to_r(a):
    n1, n2 = a.n1, a.n2
    h = (n1 + n2) / n1 + (n1 + n2) / n2 if n1 and n2 else 4.0
    r = a.d / math.sqrt(a.d ** 2 + h)
    return {"d": a.d, "r": r, "a_factor": h, "note": "Borenstein 2009 ch. 7; r is point-biserial, not a Pearson r between two continuous variables"}


def cmd_r_to_d(a):
    d = 2 * a.r / math.sqrt(1 - a.r ** 2)
    return {"r": a.r, "d": d, "note": "assumes equal group sizes (Borenstein 2009 ch. 7)"}


def _two_by_two(a, measure):
    A, B, C, D = a.a, a.b, a.c, a.d
    cc = 0.0
    if 0 in (A, B, C, D):
        cc = 0.5
    A, B, C, D = A + cc, B + cc, C + cc, D + cc
    if measure == "or":
        est = (A * D) / (B * C)
        se = math.sqrt(1 / A + 1 / B + 1 / C + 1 / D)
    else:
        est = (A / (A + B)) / (C / (C + D))
        se = math.sqrt(1 / A - 1 / (A + B) + 1 / C - 1 / (C + D))
    z = zcrit(a.level)
    out = {measure: est, f"log_{measure}": math.log(est), "se_log": se,
           "ci_low": math.exp(math.log(est) - z * se), "ci_high": math.exp(math.log(est) + z * se),
           "layout": "a=exposed events, b=exposed non-events, c=unexposed events, d=unexposed non-events"}
    if cc:
        out["note"] = "0.5 added to every cell because of a zero count"
    return out


def cmd_se_from_sd(a):
    return {"se": a.sd / math.sqrt(a.n)}


def cmd_iqr_to_sd(a):
    out = {}
    if a.iqr is not None:
        out["sd_from_iqr"] = a.iqr / 1.35
        out["note_iqr"] = "IQR/1.35 assumes normality (Cochrane Handbook 6.5.2.5; Wan 2014 gives n-specific factors)"
    if a.range is not None and a.n is not None:
        n = a.n
        xi = 2 * stats.norm.ppf((n - 0.375) / (n + 0.25))
        out["sd_from_range"] = a.range / xi
        out["note_range"] = "Wan 2014 eq. 9: range / (2 * Phi^-1((n-0.375)/(n+0.25)))"
    if not out:
        sys.exit("give --iqr, or --range with --n")
    return out


def build():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--json", action="store_true", help="print JSON instead of key=value lines")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("ci-to-se", help="CI -> SE"); s.set_defaults(fn=cmd_ci_to_se)
    s.add_argument("--low", type=float, required=True); s.add_argument("--high", type=float, required=True)
    s.add_argument("--estimate", type=float, help="point estimate, to check it sits at the CI midpoint")
    s.add_argument("--scale", choices=["normal", "log", "logit", "fisherz"], default="normal")
    s.add_argument("--level", type=float, default=0.95)

    s = sub.add_parser("auc-se", help="AUC + group sizes -> SE (Hanley-McNeil)"); s.set_defaults(fn=cmd_auc_se)
    s.add_argument("--auc", type=float, required=True); s.add_argument("--n-pos", type=float, required=True)
    s.add_argument("--n-neg", type=float, required=True); s.add_argument("--level", type=float, default=0.95)

    s = sub.add_parser("spearman-var", help="Spearman rho + n -> z-scale variance"); s.set_defaults(fn=cmd_spearman_var)
    s.add_argument("--rho", type=float, required=True); s.add_argument("--n", type=float, required=True)

    for name, fn, extra in (("t-to-d", cmd_t_to_d, "t"), ("f-to-d", cmd_f_to_d, "F"), ("p-to-d", cmd_p_to_d, "p")):
        s = sub.add_parser(name, help=f"{extra} + n1, n2 -> d and Hedges g"); s.set_defaults(fn=fn)
        s.add_argument(f"--{extra}", type=float, required=True, dest=extra)
        s.add_argument("--n1", type=float, required=True); s.add_argument("--n2", type=float, required=True)
        if extra != "t":
            s.add_argument("--sign", type=float, default=1, help="+1 or -1: direction of the difference (group1 - group2)")

    s = sub.add_parser("means-to-smd", help="two-group means/SDs -> Hedges g"); s.set_defaults(fn=cmd_means_to_smd)
    for k in ("m1", "sd1", "n1", "m2", "sd2", "n2"):
        s.add_argument(f"--{k}", type=float, required=True)

    s = sub.add_parser("d-to-r", help="d -> point-biserial r"); s.set_defaults(fn=cmd_d_to_r)
    s.add_argument("--d", type=float, required=True); s.add_argument("--n1", type=float); s.add_argument("--n2", type=float)
    s = sub.add_parser("r-to-d", help="r -> d"); s.set_defaults(fn=cmd_r_to_d)
    s.add_argument("--r", type=float, required=True)

    for name, m in (("or-from-2x2", "or"), ("rr-from-2x2", "rr")):
        s = sub.add_parser(name, help=f"2x2 cells -> {m.upper()} with log SE"); s.set_defaults(fn=lambda a, m=m: _two_by_two(a, m))
        for k in "abcd":
            s.add_argument(f"--{k}", type=float, required=True)
        s.add_argument("--level", type=float, default=0.95)

    s = sub.add_parser("se-from-sd", help="SD + n -> SE"); s.set_defaults(fn=cmd_se_from_sd)
    s.add_argument("--sd", type=float, required=True); s.add_argument("--n", type=float, required=True)

    s = sub.add_parser("iqr-to-sd", help="IQR or range -> approximate SD"); s.set_defaults(fn=cmd_iqr_to_sd)
    s.add_argument("--iqr", type=float); s.add_argument("--range", type=float); s.add_argument("--n", type=float)
    return p


def main(argv=None) -> int:
    a = build().parse_args(argv)
    out = a.fn(a)
    if a.json:
        print(json.dumps(out, indent=2))
    else:
        for k, v in out.items():
            print(f"{k}={v:.6g}" if isinstance(v, float) else f"{k}={v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
