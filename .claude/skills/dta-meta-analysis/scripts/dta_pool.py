#!/usr/bin/env python3
"""Diagnostic test accuracy (DTA) meta-analysis of 2x2 tables.

Subcommands
  validate  check a dta.csv, describe the pooling units it supports, exit 2 if unusable
  run       fit the models and write results.json, summary.md, per_study.csv, sroc.*, forest.*

Input: a CSV with at least study_id, TP, FP, FN, TN. Recommended extra columns:
label, instrument, threshold, reference_standard. Any other column is kept and
can be used with --subgroup or --filter.

Models (see references/methods.md in the skill folder)
  per study   sensitivity, specificity, LR+, LR-, DOR with exact (Clopper-Pearson)
              and Wilson CIs; 0.5 added to all four cells of a study only when
              one of them is zero, and only for LR/DOR/normal-approximation
              inputs (sens/spec and their exact CIs use the raw counts)
  glmm        bivariate binomial-normal GLMM (Chu & Cole 2006), marginal
              likelihood by adaptive Gauss-Hermite quadrature, ML
  reml / ml   bivariate normal-approximation model (Reitsma 2005) on logit
              sensitivity and logit specificity with known within-study variances
  hsroc       Rutter-Gatsonis HSROC parameters derived from the bivariate fit
              (Harbord 2007 equivalence) to draw the SROC curve
  univariate  DerSimonian-Laird and fixed-effect pooling of logit sens and logit
              spec, used as a sanity check and as the fallback when k < 4

Exit status: 0 success, 1 analysis error, 2 input error.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
import warnings
from collections import OrderedDict, defaultdict

try:
    import numpy as np
    from scipy import optimize, stats
    from scipy.special import expit as _sp_expit, gammaln, logsumexp
except ImportError:  # python3 -I hides the user site; re-add that one trusted dir
    import site
    sys.path.append(site.getusersitepackages())
    try:
        import numpy as np
        from scipy import optimize, stats
        from scipy.special import expit as _sp_expit, gammaln, logsumexp
    except ImportError:
        sys.exit("numpy/scipy/matplotlib are required: python3 -m pip install --user --break-system-packages numpy scipy matplotlib")

VERSION = "1.0.0"
REQUIRED = ["study_id", "TP", "FP", "FN", "TN"]
RECOMMENDED = ["label", "instrument", "threshold", "reference_standard"]
CHI2_95_2 = stats.chi2.ppf(0.95, 2)
Z95 = stats.norm.ppf(0.975)

# Palette (dataviz skill reference palette, light mode)
C_STUDY = "#2a78d6"
C_SUMMARY = "#eb6834"
C_CONF = "#eb6834"
C_PRED = "#6250d6"
C_CURVE = "#1baf7a"
C_TEXT = "#0b0b0b"
C_MUTED = "#52514e"
C_GRID = "#d9d8d4"


# ----------------------------------------------------------------------------
# small helpers
# ----------------------------------------------------------------------------
def expit(x):
    return _sp_expit(np.asarray(x, dtype=float))  # overflow-safe


def logit(p):
    p = np.asarray(p, dtype=float)
    return np.log(p / (1.0 - p))


def log_expit(x):
    return -np.logaddexp(0.0, -x)


def log1m_expit(x):
    return -np.logaddexp(0.0, x)


def fmt(x, nd=3):
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return "NA"
    return f"{x:.{nd}f}"


def ci_str(est, lo, hi, nd=3):
    return f"{fmt(est, nd)} ({fmt(lo, nd)} to {fmt(hi, nd)})"


def warn(msgs, text):
    msgs.append(text)
    print("WARNING: " + text, file=sys.stderr)


def clopper_pearson(x, n, alpha=0.05):
    if n == 0:
        return (float("nan"), float("nan"))
    lo = 0.0 if x == 0 else float(stats.beta.ppf(alpha / 2, x, n - x + 1))
    hi = 1.0 if x == n else float(stats.beta.ppf(1 - alpha / 2, x + 1, n - x))
    return (lo, hi)


def wilson(x, n, alpha=0.05):
    if n == 0:
        return (float("nan"), float("nan"))
    z = stats.norm.ppf(1 - alpha / 2)
    p = x / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


# ----------------------------------------------------------------------------
# input
# ----------------------------------------------------------------------------
def read_dta(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            raise ValueError("empty CSV")
        fields = [f.strip() for f in reader.fieldnames]
        rows = []
        for i, r in enumerate(reader, start=2):
            rows.append({k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in r.items()})
    missing = [c for c in REQUIRED if c not in fields]
    if missing:
        raise ValueError(f"missing required column(s): {', '.join(missing)}; have: {', '.join(fields)}")
    return fields, rows


def parse_counts(rows, msgs, label_col=None):
    """Coerce TP/FP/FN/TN to ints; drop rows that cannot be used. label_col: column to use as the study label."""
    kept = []
    for i, r in enumerate(rows, start=2):
        if label_col and r.get(label_col):
            r = dict(r, label=r[label_col])
        try:
            cells = [int(float(r[c])) for c in ("TP", "FP", "FN", "TN")]
        except (TypeError, ValueError):
            warn(msgs, f"row {i} ({r.get('study_id')}): non-numeric 2x2 cell, row dropped")
            continue
        if min(cells) < 0:
            warn(msgs, f"row {i} ({r.get('study_id')}): negative cell, row dropped")
            continue
        tp, fp, fn, tn = cells
        if tp + fn == 0 or tn + fp == 0:
            warn(msgs, f"row {i} ({r.get('study_id')}): no diseased or no non-diseased participants, row dropped")
            continue
        r = dict(r)
        r.update(TP=tp, FP=fp, FN=fn, TN=tn, _row=i)
        for c in RECOMMENDED:
            if not r.get(c):
                r[c] = r.get("study_id", "") if c == "label" else ""
        kept.append(r)
    return kept


def parse_threshold(t):
    if t is None or t == "":
        return None
    s = str(t).replace("≥", "").replace(">=", "").replace("<=", "").replace(">", "").replace("<", "").strip()
    try:
        return float(s)
    except ValueError:
        return None


def apply_filters(rows, filters, msgs):
    for col, val in filters:
        before = len(rows)
        rows = [r for r in rows if str(r.get(col, "")) == val]
        print(f"filter {col}={val!r}: {before} -> {len(rows)} rows", file=sys.stderr)
    return rows


def one_per_study(rows, rule, msgs):
    """Reduce to one 2x2 per study_id. rule: None | 'closest:X' | 'youden' | 'first' | 'largest'."""
    groups = OrderedDict()
    for r in rows:
        groups.setdefault(r["study_id"], []).append(r)
    multi = {k: v for k, v in groups.items() if len(v) > 1}
    if not multi:
        return rows
    desc = ", ".join(f"{k} ({len(v)} rows)" for k, v in multi.items())
    if rule is None:
        warn(msgs, f"{len(multi)} study_id(s) contribute more than one 2x2 table: {desc}. "
                   "The bivariate model assumes one table per study; these rows are treated as "
                   "independent studies, which understates heterogeneity and overstates precision. "
                   "Use --one-per-study closest:X | youden | largest | first, or --filter.")
        return rows
    out = []
    for k, v in groups.items():
        if len(v) == 1:
            out.append(v[0])
            continue
        if rule.startswith("closest:"):
            target = float(rule.split(":", 1)[1])
            scored = [(abs((parse_threshold(r["threshold"]) if parse_threshold(r["threshold"]) is not None else float("inf")) - target), i, r)
                      for i, r in enumerate(v)]
            pick = min(scored)[2]
        elif rule == "youden":
            pick = max(v, key=lambda r: r["TP"] / (r["TP"] + r["FN"]) + r["TN"] / (r["TN"] + r["FP"]) - 1)
        elif rule == "largest":
            pick = max(v, key=lambda r: r["TP"] + r["FP"] + r["FN"] + r["TN"])
        elif rule == "first":
            pick = v[0]
        else:
            raise ValueError(f"unknown --one-per-study rule {rule!r}")
        out.append(pick)
    warn(msgs, f"--one-per-study {rule}: kept one row for each of {len(multi)} multi-row study_id(s): {desc}")
    return out


# ----------------------------------------------------------------------------
# per-study estimates
# ----------------------------------------------------------------------------
def per_study(rows, cc_all=False):
    any_zero = any(min(r["TP"], r["FP"], r["FN"], r["TN"]) == 0 for r in rows)
    out = []
    for r in rows:
        tp, fp, fn, tn = r["TP"], r["FP"], r["FN"], r["TN"]
        n1, n0 = tp + fn, tn + fp
        zero = min(tp, fp, fn, tn) == 0
        cc = 0.5 if (zero or (cc_all and any_zero)) else 0.0
        tpc, fpc, fnc, tnc = tp + cc, fp + cc, fn + cc, tn + cc
        sens, spec = tp / n1, tn / n0
        sensc, specc = tpc / (tpc + fnc), tnc / (tnc + fpc)
        d = OrderedDict()
        d["study_id"] = r["study_id"]
        d["label"] = r["label"]
        d["instrument"] = r["instrument"]
        d["threshold"] = r["threshold"]
        d["reference_standard"] = r["reference_standard"]
        d.update(TP=tp, FP=fp, FN=fn, TN=tn, n_diseased=n1, n_nondiseased=n0, n=n1 + n0)
        d["continuity_correction"] = cc
        d["sens"] = sens
        d["sens_cp_lo"], d["sens_cp_hi"] = clopper_pearson(tp, n1)
        d["sens_wilson_lo"], d["sens_wilson_hi"] = wilson(tp, n1)
        d["spec"] = spec
        d["spec_cp_lo"], d["spec_cp_hi"] = clopper_pearson(tn, n0)
        d["spec_wilson_lo"], d["spec_wilson_hi"] = wilson(tn, n0)
        # LR and DOR on corrected cells (Wald CIs on the log scale)
        lrp = sensc / (1 - specc)
        lrn = (1 - sensc) / specc
        dor = (tpc * tnc) / (fpc * fnc)
        se_lrp = math.sqrt((1 - sensc) / tpc + specc / fpc)
        se_lrn = math.sqrt(sensc / fnc + (1 - specc) / tnc)
        se_dor = math.sqrt(1 / tpc + 1 / fpc + 1 / fnc + 1 / tnc)
        d["LR_pos"], d["LR_pos_lo"], d["LR_pos_hi"] = lrp, lrp * math.exp(-Z95 * se_lrp), lrp * math.exp(Z95 * se_lrp)
        d["LR_neg"], d["LR_neg_lo"], d["LR_neg_hi"] = lrn, lrn * math.exp(-Z95 * se_lrn), lrn * math.exp(Z95 * se_lrn)
        d["DOR"], d["DOR_lo"], d["DOR_hi"] = dor, dor * math.exp(-Z95 * se_dor), dor * math.exp(Z95 * se_dor)
        d["lnDOR"], d["se_lnDOR"] = math.log(dor), se_dor
        # normal-approximation inputs
        d["logit_sens"], d["var_logit_sens"] = math.log(tpc / fnc), 1 / tpc + 1 / fnc
        d["logit_spec"], d["var_logit_spec"] = math.log(tnc / fpc), 1 / tnc + 1 / fpc
        d["ESS"] = 4 * n1 * n0 / (n1 + n0)
        for extra in r:
            if extra not in d and not extra.startswith("_"):
                d[extra] = r[extra]
        out.append(d)
    return out


# ----------------------------------------------------------------------------
# univariate pooling (DerSimonian-Laird) on the logit scale
# ----------------------------------------------------------------------------
def dl_pool(y, v):
    y, v = np.asarray(y, float), np.asarray(v, float)
    k = len(y)
    w = 1 / v
    yf = np.sum(w * y) / np.sum(w)
    se_f = math.sqrt(1 / np.sum(w))
    q = float(np.sum(w * (y - yf) ** 2))
    c = np.sum(w) - np.sum(w ** 2) / np.sum(w)
    tau2 = max(0.0, (q - (k - 1)) / c) if k > 1 else 0.0
    wr = 1 / (v + tau2)
    yr = np.sum(wr * y) / np.sum(wr)
    se_r = math.sqrt(1 / np.sum(wr))
    i2 = max(0.0, (q - (k - 1)) / q) if q > 0 and k > 1 else 0.0
    p_q = float(stats.chi2.sf(q, k - 1)) if k > 1 else float("nan")
    return dict(k=k, fixed=yf, fixed_se=se_f, random=yr, random_se=se_r, tau2=tau2,
                Q=q, Q_df=k - 1, Q_p=p_q, I2=i2)


def univariate_block(ps):
    out = {}
    for name in ("sens", "spec"):
        y = [d[f"logit_{name}"] for d in ps]
        v = [d[f"var_logit_{name}"] for d in ps]
        r = dl_pool(y, v)
        for kind in ("fixed", "random"):
            est, se = r[kind], r[f"{kind}_se"]
            r[f"{kind}_prop"] = float(expit(est))
            r[f"{kind}_prop_lo"] = float(expit(est - Z95 * se))
            r[f"{kind}_prop_hi"] = float(expit(est + Z95 * se))
        out[name] = r
    return out


# ----------------------------------------------------------------------------
# bivariate normal-approximation model (Reitsma 2005), ML / REML
# ----------------------------------------------------------------------------
def sigma_from_phi(phi):
    t1, t2 = math.exp(phi[0]), math.exp(phi[1])
    rho = math.tanh(phi[2])
    return np.array([[t1 * t1, rho * t1 * t2], [rho * t1 * t2, t2 * t2]])


def phi_from_sigma(S):
    t1, t2 = math.sqrt(max(S[0, 0], 1e-8)), math.sqrt(max(S[1, 1], 1e-8))
    rho = S[0, 1] / (t1 * t2)
    rho = max(-0.999, min(0.999, rho))
    return np.array([math.log(t1), math.log(t2), math.atanh(rho)])


def design(X):
    """X: (k, p) covariate matrix -> list of (2, 2p) design matrices [x_i' (x) I_2]."""
    k, p = X.shape
    D = np.zeros((k, 2, 2 * p))
    for i in range(k):
        D[i, 0, 0::2] = X[i]
        D[i, 1, 1::2] = X[i]
    return D


def gls_beta(Y, S_within, Sigma, D):
    k = Y.shape[0]
    p2 = D.shape[2]
    A = np.zeros((p2, p2))
    b = np.zeros(p2)
    for i in range(k):
        Vi = np.linalg.inv(Sigma + S_within[i])
        A += D[i].T @ Vi @ D[i]
        b += D[i].T @ Vi @ Y[i]
    cov = np.linalg.inv(A)
    return cov @ b, cov, A


def nll_normal(phi, Y, S_within, D, reml):
    Sigma = sigma_from_phi(phi)
    try:
        beta, cov, A = gls_beta(Y, S_within, Sigma, D)
    except np.linalg.LinAlgError:
        return 1e10
    val = 0.0
    for i in range(Y.shape[0]):
        V = Sigma + S_within[i]
        r = Y[i] - D[i] @ beta
        sign, logdet = np.linalg.slogdet(V)
        if sign <= 0:
            return 1e10
        val += logdet + r @ np.linalg.solve(V, r) + 2 * math.log(2 * math.pi)
    if reml:
        sign, logdet = np.linalg.slogdet(A)
        val += logdet - D.shape[2] * math.log(2 * math.pi)
    return 0.5 * val


def fit_normal(ps, X, reml=True, msgs=None):
    Y = np.array([[d["logit_sens"], d["logit_spec"]] for d in ps])
    S_within = np.array([np.diag([d["var_logit_sens"], d["var_logit_spec"]]) for d in ps])
    D = design(X)
    starts = [np.array([math.log(0.5), math.log(0.5), 0.0]),
              np.array([math.log(0.2), math.log(0.2), -0.3]),
              np.array([math.log(1.0), math.log(1.0), -0.8])]
    best = None
    for s in starts:
        res = optimize.minimize(nll_normal, s, args=(Y, S_within, D, reml), method="Nelder-Mead",
                                options=dict(xatol=1e-7, fatol=1e-9, maxiter=4000))
        res = optimize.minimize(nll_normal, res.x, args=(Y, S_within, D, reml), method="BFGS",
                                options=dict(gtol=1e-7))
        if best is None or res.fun < best.fun:
            best = res
    phi = best.x
    Sigma = sigma_from_phi(phi)
    beta, cov, _ = gls_beta(Y, S_within, Sigma, D)
    return dict(method="REML" if reml else "ML", beta=beta, cov_beta=cov, Sigma=Sigma, phi=phi,
                loglik=-best.fun, nparams=len(beta) + 3, converged=bool(best.success or best.fun < 1e9),
                k=Y.shape[0])


# ----------------------------------------------------------------------------
# bivariate binomial GLMM (Chu & Cole 2006), adaptive Gauss-Hermite quadrature
# ----------------------------------------------------------------------------
def _gh(Q):
    z, w = np.polynomial.hermite.hermgauss(Q)
    Z1, Z2 = np.meshgrid(z, z, indexing="ij")
    W = np.outer(w, w)
    nodes = np.stack([Z1.ravel(), Z2.ravel()], axis=1)  # (Q^2, 2)
    return nodes, np.log(W.ravel()), np.sum(nodes ** 2, axis=1)


def glmm_loglik(theta, tp, n1, tn, n0, X, nodes, logw, zz):
    """Marginal log-likelihood of the bivariate binomial-normal model.

    theta = (beta (2p), log tau1, log tau2, atanh rho); eta_i = X_i beta on each margin.
    """
    k, p = X.shape
    beta = theta[: 2 * p]
    eta1 = X @ beta[0::2]
    eta2 = X @ beta[1::2]
    Sigma = sigma_from_phi(theta[2 * p:])
    try:
        Sinv = np.linalg.inv(Sigma)
    except np.linalg.LinAlgError:
        return -1e10
    sign, logdetS = np.linalg.slogdet(Sigma)
    if sign <= 0:
        return -1e10
    lognorm = -0.5 * (2 * math.log(2 * math.pi) + logdetS)

    def h(u):  # u: (k, m, 2) -> (k, m) log integrand
        e1 = eta1[:, None] + u[..., 0]
        e2 = eta2[:, None] + u[..., 1]
        ll = (tp[:, None] * log_expit(e1) + (n1 - tp)[:, None] * log1m_expit(e1)
              + tn[:, None] * log_expit(e2) + (n0 - tn)[:, None] * log1m_expit(e2))
        quad = -0.5 * (Sinv[0, 0] * u[..., 0] ** 2 + 2 * Sinv[0, 1] * u[..., 0] * u[..., 1] + Sinv[1, 1] * u[..., 1] ** 2)
        return ll + quad + lognorm

    # Newton iterations for the per-study mode (objective strictly concave)
    u = np.zeros((k, 2))
    for _ in range(50):
        p1, p2 = expit(eta1 + u[:, 0]), expit(eta2 + u[:, 1])
        g = np.stack([tp - n1 * p1, tn - n0 * p2], axis=1) - u @ Sinv
        a = n1 * p1 * (1 - p1) + Sinv[0, 0]
        d = n0 * p2 * (1 - p2) + Sinv[1, 1]
        b = Sinv[0, 1]
        det = a * d - b * b
        step = np.stack([(d * g[:, 0] - b * g[:, 1]) / det, (-b * g[:, 0] + a * g[:, 1]) / det], axis=1)
        u = u + step
        if np.max(np.abs(step)) < 1e-9:
            break
    p1, p2 = expit(eta1 + u[:, 0]), expit(eta2 + u[:, 1])
    a = n1 * p1 * (1 - p1) + Sinv[0, 0]
    d = n0 * p2 * (1 - p2) + Sinv[1, 1]
    b = np.full(k, Sinv[0, 1])
    # L = chol(H^-1) where H = [[a,b],[b,d]]; H^-1 = [[d,-b],[-b,a]]/det
    det = a * d - b * b
    inv11, inv12, inv22 = d / det, -b / det, a / det
    L11 = np.sqrt(inv11)
    L21 = inv12 / L11
    L22 = np.sqrt(np.maximum(inv22 - L21 ** 2, 1e-300))
    logdetL = np.log(L11) + np.log(L22)
    # transformed nodes: u_hat + sqrt(2) L z
    s2 = math.sqrt(2.0)
    z1, z2 = nodes[:, 0][None, :], nodes[:, 1][None, :]
    U = np.empty((k, nodes.shape[0], 2))
    U[..., 0] = u[:, 0:1] + s2 * L11[:, None] * z1
    U[..., 1] = u[:, 1:2] + s2 * (L21[:, None] * z1 + L22[:, None] * z2)
    vals = h(U) + zz[None, :] + logw[None, :]
    per_study = math.log(2.0) + logdetL + logsumexp(vals, axis=1)
    # binomial coefficients (constants) so the value is a proper log-likelihood
    const = (gammaln(n1 + 1) - gammaln(tp + 1) - gammaln(n1 - tp + 1)
             + gammaln(n0 + 1) - gammaln(tn + 1) - gammaln(n0 - tn + 1))
    return float(np.sum(per_study + const))


def num_hessian(f, x, h=1e-4):
    n = len(x)
    H = np.zeros((n, n))
    f0 = f(x)
    for i in range(n):
        for j in range(i, n):
            xpp = x.copy(); xpp[i] += h; xpp[j] += h
            xpm = x.copy(); xpm[i] += h; xpm[j] -= h
            xmp = x.copy(); xmp[i] -= h; xmp[j] += h
            xmm = x.copy(); xmm[i] -= h; xmm[j] -= h
            if i == j:
                xp = x.copy(); xp[i] += h
                xm = x.copy(); xm[i] -= h
                H[i, i] = (f(xp) - 2 * f0 + f(xm)) / (h * h)
            else:
                H[i, j] = H[j, i] = (f(xpp) - f(xpm) - f(xmp) + f(xmm)) / (4 * h * h)
    return H


def fit_glmm(ps, X, start=None, Q=15, msgs=None):
    tp = np.array([d["TP"] for d in ps], float)
    n1 = np.array([d["n_diseased"] for d in ps], float)
    tn = np.array([d["TN"] for d in ps], float)
    n0 = np.array([d["n_nondiseased"] for d in ps], float)
    nodes, logw, zz = _gh(Q)
    k, p = X.shape

    def nll(theta):
        return -glmm_loglik(theta, tp, n1, tn, n0, X, nodes, logw, zz)

    if start is None:
        start = np.concatenate([np.tile([1.0, 1.0], p), [math.log(0.5), math.log(0.5), 0.0]])
    lo_tau = math.log(1e-3)
    bounds = [(-12, 12)] * (2 * p) + [(lo_tau, math.log(20)), (lo_tau, math.log(20)), (-6, 6)]
    best = None
    for s in [start, np.concatenate([start[: 2 * p], [math.log(0.3), math.log(0.3), -0.2]])]:
        res = optimize.minimize(nll, s, method="L-BFGS-B", bounds=bounds,
                                options=dict(ftol=1e-12, gtol=1e-8, maxiter=2000))
        if best is None or res.fun < best.fun:
            best = res
    theta = best.x
    at_boundary = [bool(theta[2 * p + j] <= lo_tau + 1e-6) for j in range(2)]
    H = num_hessian(nll, theta, h=1e-4)
    try:
        cov = np.linalg.inv(H)
        pd = bool(np.all(np.linalg.eigvalsh(H) > 0))
    except np.linalg.LinAlgError:
        cov, pd = np.linalg.pinv(H), False
    if not pd and msgs is not None:
        warn(msgs, "GLMM: observed information is not positive definite; standard errors are unreliable "
                   "(usually a between-study variance at its lower bound).")
    beta = theta[: 2 * p]
    return dict(method="GLMM-AGHQ", beta=beta, cov_beta=cov[: 2 * p, : 2 * p], Sigma=sigma_from_phi(theta[2 * p:]),
                phi=theta[2 * p:], cov_theta=cov, loglik=-best.fun, nparams=len(theta), converged=bool(best.success),
                k=k, Q=Q, tau_at_boundary=at_boundary, hessian_pd=pd, message=str(best.message))


# ----------------------------------------------------------------------------
# summaries derived from a bivariate fit
# ----------------------------------------------------------------------------
def hsroc_from_bivariate(mu_a, mu_b, Sigma):
    """Harbord 2007 equivalence. mu_a = E[logit sens], mu_b = E[logit spec]."""
    sa, sb = math.sqrt(Sigma[0, 0]), math.sqrt(Sigma[1, 1])
    sab = Sigma[0, 1]
    beta = math.log(sb / sa)
    r = math.sqrt(sb / sa)
    Lambda = r * mu_a + mu_b / r
    Theta = 0.5 * (r * mu_a - mu_b / r)
    var_alpha = 2 * (sa * sb + sab)
    var_theta = 0.5 * (sa * sb - sab)
    return dict(Lambda=Lambda, Theta=Theta, beta=beta, var_alpha=max(var_alpha, 0.0), var_theta=max(var_theta, 0.0),
                rho_sens_spec=sab / (sa * sb))


def hsroc_curve(h, fpr):
    """Sensitivity on the HSROC curve at false-positive rate fpr."""
    lf = logit(np.asarray(fpr, float))
    return expit(h["Lambda"] * math.exp(-h["beta"] / 2) + math.exp(-h["beta"]) * lf)


def summary_block(fit, idx=(0, 1)):
    """Pooled sens/spec, DOR, LRs with delta-method CIs from fit['beta'] and fit['cov_beta'] at index pair idx."""
    a, b = idx
    mu_a, mu_b = float(fit["beta"][a]), float(fit["beta"][b])
    V = fit["cov_beta"]
    vaa, vbb, vab = float(V[a, a]), float(V[b, b]), float(V[a, b])
    sens, spec = float(expit(mu_a)), float(expit(mu_b))
    out = OrderedDict()
    out["logit_sens"], out["se_logit_sens"] = mu_a, math.sqrt(vaa)
    out["logit_spec"], out["se_logit_spec"] = mu_b, math.sqrt(vbb)
    out["sens"], out["sens_lo"], out["sens_hi"] = sens, float(expit(mu_a - Z95 * math.sqrt(vaa))), float(expit(mu_a + Z95 * math.sqrt(vaa)))
    out["spec"], out["spec_lo"], out["spec_hi"] = spec, float(expit(mu_b - Z95 * math.sqrt(vbb))), float(expit(mu_b + Z95 * math.sqrt(vbb)))
    lndor = mu_a + mu_b
    se_lndor = math.sqrt(max(vaa + vbb + 2 * vab, 0))
    out["DOR"], out["DOR_lo"], out["DOR_hi"] = math.exp(lndor), math.exp(lndor - Z95 * se_lndor), math.exp(lndor + Z95 * se_lndor)
    lrp = sens / (1 - spec)
    g = np.array([1 - sens, spec])
    se = math.sqrt(max(g @ np.array([[vaa, vab], [vab, vbb]]) @ g, 0))
    out["LR_pos"], out["LR_pos_lo"], out["LR_pos_hi"] = lrp, lrp * math.exp(-Z95 * se), lrp * math.exp(Z95 * se)
    lrn = (1 - sens) / spec
    g = np.array([-sens, -(1 - spec)])
    se = math.sqrt(max(g @ np.array([[vaa, vab], [vab, vbb]]) @ g, 0))
    out["LR_neg"], out["LR_neg_lo"], out["LR_neg_hi"] = lrn, lrn * math.exp(-Z95 * se), lrn * math.exp(Z95 * se)
    out["cov_logit"] = [[vaa, vab], [vab, vbb]]
    return out


def heterogeneity_block(fit, ps, uni):
    S = fit["Sigma"]
    tau1, tau2 = math.sqrt(S[0, 0]), math.sqrt(S[1, 1])
    rho = S[0, 1] / (tau1 * tau2) if tau1 > 0 and tau2 > 0 else float("nan")
    out = OrderedDict()
    out["tau_logit_sens"], out["tau_logit_spec"], out["rho_sens_spec"] = tau1, tau2, rho
    out["Sigma_between"] = S.tolist()
    # 95% prediction interval for a new study's sens and spec (marginal, logit scale)
    V = fit["cov_beta"][:2, :2]
    for j, name in enumerate(("sens", "spec")):
        se = math.sqrt(S[j, j] + V[j, j])
        out[f"pred_{name}_lo"] = float(expit(fit["beta"][j] - Z95 * se))
        out[f"pred_{name}_hi"] = float(expit(fit["beta"][j] + Z95 * se))
    # Jackson, White & Riley 2012 multivariate I^2 (ratio of generalized variances) -- optional
    k = len(ps)
    Sw = np.array([np.diag([d["var_logit_sens"], d["var_logit_spec"]]) for d in ps])
    A_fe = sum(np.linalg.inv(s) for s in Sw)
    A_re = sum(np.linalg.inv(S + s) for s in Sw)
    R2 = np.linalg.det(np.linalg.inv(A_re)) / np.linalg.det(np.linalg.inv(A_fe))
    out["I2_multivariate_JWR2012"] = float(max(0.0, 1 - 1 / R2)) if R2 > 0 else float("nan")
    # Zhou & Dendukuri 2014-style generalised-variance I^2 with a 'typical' within-study covariance
    Sbar = np.mean(Sw, axis=0)
    out["I2_bivariate_ZD2014_style"] = float(max(0.0, 1 - math.sqrt(np.linalg.det(Sbar) / np.linalg.det(S + Sbar))))
    out["I2_univariate_sens"], out["I2_univariate_spec"] = uni["sens"]["I2"], uni["spec"]["I2"]
    out["note"] = ("I^2 statistics are reported for completeness only; for DTA the prediction region and the "
                   "between-study SDs are the recommended descriptions of heterogeneity (Cochrane DTA Handbook ch. 10).")
    return out


def deeks_test(ps):
    k = len(ps)
    if k < 10:
        return dict(performed=False, reason=f"k = {k} < 10; Deeks' test is underpowered and not reported (Deeks 2005)")
    y = np.array([d["lnDOR"] for d in ps])
    x = 1 / np.sqrt(np.array([d["ESS"] for d in ps]))
    w = np.array([d["ESS"] for d in ps])
    Xd = np.column_stack([np.ones(k), x])
    W = np.diag(w)
    coef = np.linalg.solve(Xd.T @ W @ Xd, Xd.T @ W @ y)
    resid = y - Xd @ coef
    s2 = float(resid @ W @ resid) / (k - 2)
    cov = s2 * np.linalg.inv(Xd.T @ W @ Xd)
    t = coef[1] / math.sqrt(cov[1, 1])
    p = 2 * stats.t.sf(abs(t), k - 2)
    return dict(performed=True, k=k, intercept=float(coef[0]), slope=float(coef[1]), slope_se=float(math.sqrt(cov[1, 1])),
                t=float(t), p=float(p), interpretation=("asymmetry suggested (p < 0.10)" if p < 0.10 else "no significant asymmetry (p >= 0.10)"))


def ellipse_points(mu, cov, scale=math.sqrt(CHI2_95_2), n=200):
    L = np.linalg.cholesky(cov)
    t = np.linspace(0, 2 * math.pi, n)
    circ = np.stack([np.cos(t), np.sin(t)])
    pts = (mu[:, None] + scale * L @ circ).T
    return pts  # (n, 2) on logit scale: (logit sens, logit spec)


# ----------------------------------------------------------------------------
# plots
# ----------------------------------------------------------------------------
def _mpl():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "sans-serif", "font.size": 10, "axes.edgecolor": C_MUTED,
                         "axes.labelcolor": C_TEXT, "xtick.color": C_MUTED, "ytick.color": C_MUTED,
                         "axes.spines.top": False, "axes.spines.right": False, "svg.fonttype": "none"})
    return plt


def plot_sroc(ps, fit, hs, outbase, title, show_regions=True, uni_point=None):
    plt = _mpl()
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot([0, 1], [0, 1], color=C_GRID, lw=1, ls=":", zorder=1)
    n = np.array([d["n"] for d in ps], float)
    size = 30 + 300 * n / n.max()
    ax.scatter([1 - d["spec"] for d in ps], [d["sens"] for d in ps], s=size, facecolor=C_STUDY, alpha=0.35,
               edgecolor=C_STUDY, lw=1, zorder=3, label=f"Studies (k = {len(ps)}, area ∝ n)")
    handles_extra = []
    if fit is not None:
        mu = fit["beta"][:2]
        if show_regions:
            conf = ellipse_points(mu, fit["cov_beta"][:2, :2])
            ax.plot(1 - expit(conf[:, 1]), expit(conf[:, 0]), color=C_CONF, lw=1.5, zorder=4, label="95% confidence region")
            try:
                pred = ellipse_points(mu, fit["cov_beta"][:2, :2] + fit["Sigma"])
                ax.plot(1 - expit(pred[:, 1]), expit(pred[:, 0]), color=C_PRED, lw=1.5, ls="--", zorder=4, label="95% prediction region")
            except np.linalg.LinAlgError:
                pass
        if hs is not None:
            fprs = 1 - expit(np.array([d["logit_spec"] for d in ps]))  # continuity-corrected where a cell is zero
            lo, hi = max(1e-4, fprs.min()), min(1 - 1e-4, fprs.max())
            if hi > lo:
                xs = np.linspace(lo, hi, 200)
                ax.plot(xs, hsroc_curve(hs, xs), color=C_CURVE, lw=2, zorder=5, label="HSROC curve (observed FPR range)")
        ax.scatter([1 - expit(mu[1])], [expit(mu[0])], marker="D", s=70, color=C_SUMMARY, edgecolor="white", lw=1, zorder=6,
                   label="Summary point")
    elif uni_point is not None:
        ax.scatter([1 - uni_point[1]], [uni_point[0]], marker="D", s=70, color=C_SUMMARY, edgecolor="white", lw=1, zorder=6,
                   label="Univariate pooled point (no bivariate fit)")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_xlabel("False-positive rate (1 − specificity)")
    ax.set_ylabel("Sensitivity")
    ax.set_title(title, color=C_TEXT, loc="left", fontsize=11)
    ax.grid(color=C_GRID, lw=0.5)
    ax.legend(loc="lower right", frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(outbase + ".svg"); fig.savefig(outbase + ".png", dpi=200)
    plt.close(fig)


def plot_forest(ps, pooled, outbase, title, pooled_label="Pooled (bivariate)"):
    plt = _mpl()
    k = len(ps)
    fig = plt.figure(figsize=(11, 0.32 * (k + 3) + 1.4))
    gs = fig.add_gridspec(1, 4, width_ratios=[3.2, 2.3, 3.2, 2.3], wspace=0.05)
    ax_s = fig.add_subplot(gs[0, 0])
    tx_s = fig.add_subplot(gs[0, 1], sharey=ax_s)
    ax_p = fig.add_subplot(gs[0, 2], sharey=ax_s)
    tx_p = fig.add_subplot(gs[0, 3], sharey=ax_s)
    ys = np.arange(k, 0, -1)
    for ax, tx, name in ((ax_s, tx_s, "sens"), (ax_p, tx_p, "spec")):
        est = np.array([d[name] for d in ps])
        lo = np.array([d[f"{name}_cp_lo"] for d in ps])
        hi = np.array([d[f"{name}_cp_hi"] for d in ps])
        n = np.array([d["n_diseased" if name == "sens" else "n_nondiseased"] for d in ps], float)
        ax.hlines(ys, lo, hi, color=C_STUDY, lw=1.5)
        ax.scatter(est, ys, s=20 + 120 * n / n.max(), marker="s", color=C_STUDY, zorder=3)
        tx.axis("off")
        for y, d, e, l, h in zip(ys, ps, est, lo, hi):
            cells = f"{d['TP']}/{d['n_diseased']}" if name == "sens" else f"{d['TN']}/{d['n_nondiseased']}"
            tx.text(0.02, y, f"{cells}", va="center", fontsize=8, color=C_MUTED)
            tx.text(0.40, y, f"{e:.2f} ({l:.2f}–{h:.2f})", va="center", fontsize=8, color=C_MUTED)
        tx.text(0.02, k + 1, "n", va="center", fontsize=8, color=C_TEXT, fontweight="bold")
        tx.text(0.40, k + 1, "Estimate (95% CI)", va="center", fontsize=8, color=C_TEXT, fontweight="bold")
        if pooled is not None:
            pe, pl, ph = pooled[name], pooled[f"{name}_lo"], pooled[f"{name}_hi"]
            ax.fill([pl, pe, ph, pe], [0.0, 0.3, 0.0, -0.3], color=C_SUMMARY, zorder=4)
            ax.axvline(pe, color=C_SUMMARY, lw=0.8, ls=":")
            tx.text(0.40, 0, f"{pe:.2f} ({pl:.2f}–{ph:.2f})", va="center", fontsize=8, color=C_TEXT, fontweight="bold")
        ax.set_xlim(0, 1)
        ax.set_ylim(-1, k + 1.6)
        ax.set_xticks([0, 0.25, 0.5, 0.75, 1])
        ax.set_xlabel("Sensitivity (95% exact CI)" if name == "sens" else "Specificity (95% exact CI)")
        ax.grid(axis="x", color=C_GRID, lw=0.5)
        ax.spines["left"].set_visible(False)
        ax.tick_params(axis="y", length=0)
        tx.set_xlim(0, 1)
    labels = [d["label"] for d in ps] + ([pooled_label] if pooled is not None else [])
    ax_s.set_yticks(list(ys) + ([0] if pooled is not None else []))
    ax_s.set_yticklabels(labels, fontsize=9)
    plt.setp(ax_p.get_yticklabels(), visible=False)
    fig.suptitle(title, x=0.01, ha="left", fontsize=11, color=C_TEXT)
    fig.subplots_adjust(left=0.16, right=0.99, top=0.95, bottom=max(0.04, 0.9 / (0.32 * (k + 3) + 1.4)))
    fig.savefig(outbase + ".svg"); fig.savefig(outbase + ".png", dpi=200)
    plt.close(fig)


# ----------------------------------------------------------------------------
# validate
# ----------------------------------------------------------------------------
def cmd_validate(args):
    msgs = []
    try:
        fields, raw = read_dta(args.csv)
    except (ValueError, OSError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    rows = parse_counts(raw, msgs)
    if not rows:
        print("ERROR: no usable rows", file=sys.stderr)
        return 2
    for c in RECOMMENDED:
        if c not in fields:
            warn(msgs, f"recommended column '{c}' is missing")
    studies = OrderedDict()
    for r in rows:
        studies.setdefault(r["study_id"], []).append(r)
    zero = [r for r in rows if min(r["TP"], r["FP"], r["FN"], r["TN"]) == 0]
    print(f"rows: {len(rows)} usable of {len(raw)}; distinct study_id: {len(studies)}; rows with a zero cell: {len(zero)}")
    multi = {k: v for k, v in studies.items() if len(v) > 1}
    if multi:
        print(f"study_ids with >1 row (thresholds/instruments): {len(multi)}")
        for k, v in multi.items():
            print(f"  {k}: " + "; ".join(f"{r['instrument']}@{r['threshold']} vs {r['reference_standard']}" for r in v))
    units = defaultdict(list)
    for r in rows:
        units[(r["instrument"], r["reference_standard"])].append(r)
    print("\ncandidate pooling units (instrument x reference_standard):")
    print(f"  {'instrument':30s} {'reference_standard':28s} {'rows':>4s} {'studies':>7s}  thresholds")
    for (ins, ref), v in sorted(units.items(), key=lambda kv: -len(kv[1])):
        ns = len({r['study_id'] for r in v})
        th = sorted({str(r["threshold"]) for r in v})
        verdict = "bivariate" if ns >= 4 else ("univariate fallback only" if ns >= 2 else "do not pool")
        print(f"  {ins[:30]:30s} {ref[:28]:28s} {len(v):4d} {ns:7d}  {', '.join(th)[:40]}  -> {verdict}")
    print("\nrules: k < 4 -> no bivariate model (per-study + univariate pooling with warnings);"
          " k = 4-10 -> bivariate fit but variance components unstable; k >= 10 -> Deeks' test reported.")
    return 0


# ----------------------------------------------------------------------------
# run
# ----------------------------------------------------------------------------
def fit_bivariate(ps, X, method, msgs, Q):
    """Returns (primary_fit, comparison_fits dict)."""
    fits = {}
    reml = fit_normal(ps, X, reml=True, msgs=msgs)
    ml = fit_normal(ps, X, reml=False, msgs=msgs)
    fits["normal_reml"], fits["normal_ml"] = reml, ml
    primary = None
    if method in ("auto", "glmm"):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                start = np.concatenate([ml["beta"], ml["phi"]])
                start[-3:] = np.maximum(start[-3:], [math.log(1e-3), math.log(1e-3), -6])
                g = fit_glmm(ps, X, start=start, Q=Q, msgs=msgs)
            fits["glmm"] = g
            ok_cov = bool(np.all(np.isfinite(g["cov_beta"])) and np.all(np.diag(g["cov_beta"]) > 0))
            if g["converged"] and g["hessian_pd"] and ok_cov:
                primary = g
            else:
                why = "observed information not positive definite" if not g["hessian_pd"] else str(g.get("message"))
                warn(msgs, f"GLMM point estimates are kept in the model-comparison table but its standard errors are "
                           f"unreliable ({why}); the normal-approximation REML fit is used as the primary model.")
        except Exception as e:  # noqa: BLE001
            warn(msgs, f"GLMM fit failed ({e}); using normal-approximation REML as primary.")
    if primary is None:
        primary = reml if method in ("auto", "glmm", "reml") else ml
    return primary, fits


def subgroup_analysis(ps, col, method, msgs, Q):
    levels = []
    for d in ps:
        v = str(d.get(col, ""))
        if v not in levels:
            levels.append(v)
    if len(levels) < 2:
        warn(msgs, f"--subgroup {col}: only one level present; skipped")
        return None
    k = len(ps)
    X0 = np.ones((k, 1))
    X1 = np.zeros((k, len(levels)))
    for i, d in enumerate(ps):
        X1[i, levels.index(str(d.get(col, "")))] = 1.0
    counts = {lv: int(X1[:, j].sum()) for j, lv in enumerate(levels)}
    small = [lv for lv, c in counts.items() if c < 3]
    if small:
        warn(msgs, f"--subgroup {col}: level(s) with < 3 studies: {small}; subgroup estimates are fragile")
    use_glmm = method in ("auto", "glmm")
    if use_glmm:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                m0 = fit_normal(ps, X0, reml=False)
                f0 = fit_glmm(ps, X0, start=np.concatenate([m0["beta"], np.maximum(m0["phi"], [math.log(1e-3)] * 2 + [-6])]), Q=Q)
                m1 = fit_normal(ps, X1, reml=False)
                f1 = fit_glmm(ps, X1, start=np.concatenate([m1["beta"], np.maximum(m1["phi"], [math.log(1e-3)] * 2 + [-6])]), Q=Q)
            label = "GLMM (ML)"
        except Exception as e:  # noqa: BLE001
            warn(msgs, f"subgroup GLMM failed ({e}); using normal-approximation ML")
            use_glmm = False
    if not use_glmm:
        f0, f1 = fit_normal(ps, X0, reml=False), fit_normal(ps, X1, reml=False)
        label = "normal approximation (ML)"
    lrt = 2 * (f1["loglik"] - f0["loglik"])
    df = 2 * (len(levels) - 1)
    p = float(stats.chi2.sf(max(lrt, 0), df))
    out = OrderedDict(covariate=col, model=label, levels=[], LRT=float(lrt), df=df, p=p,
                      note="Likelihood-ratio test of a model with separate logit sens and logit spec per level "
                           "against common means, shared between-study covariance; ML fits (REML log-likelihoods "
                           "are not comparable across fixed-effect structures).")
    for j, lv in enumerate(levels):
        s = summary_block(f1, idx=(2 * j, 2 * j + 1))
        s = OrderedDict([("level", lv), ("k", counts[lv])] + list(s.items()))
        out["levels"].append(s)
    return out


def results_to_md(res, args):
    L = []
    L.append(f"# DTA meta-analysis: {res['name']}\n")
    L.append(f"Input: `{res['input']}`; {res['k']} studies after filters/selection. Generated by dta_pool.py v{VERSION}.\n")
    if res["warnings"]:
        L.append("## Warnings\n")
        for w in res["warnings"]:
            L.append(f"- {w}")
        L.append("")
    L.append("## Per-study estimates\n")
    L.append("| Study | Instrument | Threshold | Reference | TP | FP | FN | TN | Sensitivity (95% exact CI) | Specificity (95% exact CI) | LR+ | LR− | DOR |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for d in res["per_study"]:
        L.append(f"| {d['label']} | {d['instrument']} | {d['threshold']} | {d['reference_standard']} | {d['TP']} | {d['FP']} | {d['FN']} | {d['TN']} | "
                 f"{d['sens']:.2f} ({d['sens_cp_lo']:.2f}–{d['sens_cp_hi']:.2f}) | {d['spec']:.2f} ({d['spec_cp_lo']:.2f}–{d['spec_cp_hi']:.2f}) | "
                 f"{d['LR_pos']:.2f} | {d['LR_neg']:.2f} | {d['DOR']:.1f} |")
    L.append("")
    pooled = res.get("pooled")
    if pooled:
        L.append(f"## Pooled estimates ({res['primary_model']})\n")
        L.append("| Quantity | Estimate (95% CI) |")
        L.append("|---|---|")
        L.append(f"| Sensitivity | {ci_str(pooled['sens'], pooled['sens_lo'], pooled['sens_hi'])} |")
        L.append(f"| Specificity | {ci_str(pooled['spec'], pooled['spec_lo'], pooled['spec_hi'])} |")
        L.append(f"| Positive likelihood ratio | {ci_str(pooled['LR_pos'], pooled['LR_pos_lo'], pooled['LR_pos_hi'], 2)} |")
        L.append(f"| Negative likelihood ratio | {ci_str(pooled['LR_neg'], pooled['LR_neg_lo'], pooled['LR_neg_hi'], 2)} |")
        L.append(f"| Diagnostic odds ratio | {ci_str(pooled['DOR'], pooled['DOR_lo'], pooled['DOR_hi'], 1)} |")
        h = res["heterogeneity"]
        L.append(f"| 95% prediction interval, sensitivity | {fmt(h['pred_sens_lo'])} to {fmt(h['pred_sens_hi'])} |")
        L.append(f"| 95% prediction interval, specificity | {fmt(h['pred_spec_lo'])} to {fmt(h['pred_spec_hi'])} |")
        L.append(f"| Between-study SD, logit sensitivity (τ_A) | {fmt(h['tau_logit_sens'])} |")
        L.append(f"| Between-study SD, logit specificity (τ_B) | {fmt(h['tau_logit_spec'])} |")
        L.append(f"| Between-study correlation (logit sens, logit spec) | {fmt(h['rho_sens_spec'])} |")
        L.append("")
        hs = res["hsroc"]
        L.append("HSROC parameters (Harbord 2007 conversion): "
                 f"Λ = {fmt(hs['Lambda'])}, Θ = {fmt(hs['Theta'])}, β = {fmt(hs['beta'])}, "
                 f"σ²_α = {fmt(hs['var_alpha'])}, σ²_θ = {fmt(hs['var_theta'])}.\n")
        L.append("Model comparison (all fits, for the appendix):\n")
        L.append("| Model | Sens (95% CI) | Spec (95% CI) | τ_A | τ_B | ρ | log-lik |")
        L.append("|---|---|---|---|---|---|---|")
        for name, f in res["fits"].items():
            s = f["summary"]
            L.append(f"| {f['method']} | {ci_str(s['sens'], s['sens_lo'], s['sens_hi'])} | {ci_str(s['spec'], s['spec_lo'], s['spec_hi'])} | "
                     f"{fmt(math.sqrt(f['Sigma'][0][0]))} | {fmt(math.sqrt(f['Sigma'][1][1]))} | {fmt(f['rho'])} | {fmt(f['loglik'], 2)} |")
        u = res["univariate"]
        L.append(f"| Univariate DL random, logit scale | {ci_str(u['sens']['random_prop'], u['sens']['random_prop_lo'], u['sens']['random_prop_hi'])} | "
                 f"{ci_str(u['spec']['random_prop'], u['spec']['random_prop_lo'], u['spec']['random_prop_hi'])} | "
                 f"{fmt(math.sqrt(u['sens']['tau2']))} | {fmt(math.sqrt(u['spec']['tau2']))} | – | – |")
        L.append("")
        L.append(f"Optional heterogeneity statistics (see caveats in SKILL.md): multivariate I² (Jackson, White & Riley 2012) = "
                 f"{fmt(h['I2_multivariate_JWR2012'], 2)}; bivariate generalised-variance I² (Zhou & Dendukuri 2014 style) = "
                 f"{fmt(h['I2_bivariate_ZD2014_style'], 2)}; univariate I² sens = {fmt(h['I2_univariate_sens'], 2)}, spec = {fmt(h['I2_univariate_spec'], 2)}.\n")
    else:
        u = res["univariate"]
        L.append("## Univariate pooled estimates (fallback; bivariate model not fitted)\n")
        L.append("| Quantity | Fixed effect | DerSimonian–Laird random effects | τ (logit) |")
        L.append("|---|---|---|---|")
        for name, lab in (("sens", "Sensitivity"), ("spec", "Specificity")):
            r = u[name]
            L.append(f"| {lab} | {ci_str(r['fixed_prop'], r['fixed_prop_lo'], r['fixed_prop_hi'])} | "
                     f"{ci_str(r['random_prop'], r['random_prop_lo'], r['random_prop_hi'])} | {fmt(math.sqrt(r['tau2']))} |")
        L.append("")
        L.append("These are reported for description only. With so few studies the between-study variance is not "
                 "estimable, the random-effects CI is unreliable, and the correlation between sensitivity and specificity "
                 "is ignored. Prefer presenting the per-study table and forest plot and describing the range.\n")
    if res.get("subgroup"):
        sg = res["subgroup"]
        L.append(f"## Subgroup analysis by `{sg['covariate']}` ({sg['model']})\n")
        L.append("| Level | k | Sensitivity (95% CI) | Specificity (95% CI) | DOR (95% CI) |")
        L.append("|---|---|---|---|---|")
        for lv in sg["levels"]:
            L.append(f"| {lv['level']} | {lv['k']} | {ci_str(lv['sens'], lv['sens_lo'], lv['sens_hi'])} | "
                     f"{ci_str(lv['spec'], lv['spec_lo'], lv['spec_hi'])} | {ci_str(lv['DOR'], lv['DOR_lo'], lv['DOR_hi'], 1)} |")
        L.append(f"\nLikelihood-ratio test: χ² = {fmt(sg['LRT'], 2)} on {sg['df']} df, p = {fmt(sg['p'], 3)}.\n")
    dk = res["deeks"]
    L.append("## Small-study effects\n")
    if dk["performed"]:
        L.append(f"Deeks' funnel plot asymmetry test (ln DOR on 1/√ESS, weighted by ESS): slope = {fmt(dk['slope'], 2)} "
                 f"(SE {fmt(dk['slope_se'], 2)}), t = {fmt(dk['t'], 2)}, p = {fmt(dk['p'], 3)}: {dk['interpretation']}.\n")
    else:
        L.append(f"Deeks' test not performed: {dk['reason']}.\n")
    L.append("## Figures\n")
    L.append("- `sroc.svg` / `sroc.png`: SROC plot with study points (area proportional to n), summary point, 95% confidence "
             "and prediction regions, and the HSROC curve over the observed range of false-positive rates.")
    L.append("- `forest.svg` / `forest.png`: paired forest plots of sensitivity and specificity with exact 95% CIs.\n")
    L.append("## Methods paragraph (template; edit to match what was actually done)\n")
    if pooled:
        prim = res["primary_model"]
        if prim.startswith("GLMM"):
            model_txt = ("a bivariate generalised linear mixed model with binomial within-study likelihoods and "
                         "bivariate normal random effects for logit sensitivity and logit specificity (Chu & Cole 2006; "
                         "Reitsma et al. 2005), fitted by maximum likelihood with adaptive Gauss–Hermite quadrature "
                         f"({res['fits']['glmm']['Q']} nodes per dimension)")
        else:
            model_txt = ("the bivariate random-effects model of Reitsma et al. (2005) on logit sensitivity and logit "
                         f"specificity with known within-study variances, fitted by {'restricted ' if 'REML' in prim else ''}maximum likelihood")
        L.append(f"Sensitivity and specificity were pooled with {model_txt}. Summary estimates are reported with 95% "
                 "confidence intervals obtained on the logit scale; likelihood ratios and the diagnostic odds ratio were derived "
                 "from the summary point by the delta method. A summary ROC curve was obtained from the bivariate parameters "
                 "using the equivalence with the hierarchical SROC model (Harbord et al. 2007) and is shown only over the "
                 "observed range of false-positive rates, together with 95% confidence and prediction regions (Macaskill et "
                 "al., Cochrane Handbook for Systematic Reviews of Diagnostic Test Accuracy, chapter 10). Heterogeneity was "
                 "described by the prediction region and the between-study standard deviations rather than I², which is "
                 "not recommended for diagnostic accuracy meta-analysis. "
                 + ("Funnel plot asymmetry was assessed with Deeks' test (Deeks et al. 2005). " if dk["performed"] else
                    "Funnel plot asymmetry was not assessed because fewer than 10 studies were available (Deeks et al. 2005). ")
                 + "A continuity correction of 0.5 was added to all cells of a study only when a cell was zero, and only for "
                 "likelihood ratios, the diagnostic odds ratio and the normal-approximation sensitivity analyses. "
                 "Analyses used Python (numpy, scipy) with scripts generated with AI assistance (Claude, Anthropic); all "
                 "model choices and interpretations were made and checked by the review authors.")
    else:
        L.append("Because fewer than four studies contributed to this comparison, no bivariate model was fitted; sensitivity "
                 "and specificity are presented per study with exact binomial 95% confidence intervals and summarised "
                 "descriptively (Macaskill et al., Cochrane Handbook for DTA reviews, chapter 10; Takwoingi et al. 2017). "
                 "Scripts were generated with AI assistance (Claude, Anthropic); all decisions were made by the review authors.")
    L.append("")
    return "\n".join(L)


def fit_to_json(f):
    S = f["Sigma"]
    t1, t2 = math.sqrt(S[0, 0]), math.sqrt(S[1, 1])
    return OrderedDict(method=f["method"], beta=[float(x) for x in f["beta"]], cov_beta=np.asarray(f["cov_beta"]).tolist(),
                       Sigma=S.tolist(), rho=float(S[0, 1] / (t1 * t2)) if t1 > 0 and t2 > 0 else None,
                       loglik=float(f["loglik"]), nparams=int(f["nparams"]), converged=bool(f["converged"]),
                       summary=summary_block(f), **{k: v for k, v in f.items() if k in ("Q", "tau_at_boundary", "hessian_pd", "message")})


def cmd_run(args):
    msgs = []
    try:
        fields, raw = read_dta(args.csv)
    except (ValueError, OSError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    if args.label_col and args.label_col not in fields:
        print(f"ERROR: --label-col column {args.label_col!r} not in CSV", file=sys.stderr)
        return 2
    rows = parse_counts(raw, msgs, label_col=args.label_col)
    filters = []
    for f in args.filter or []:
        if "=" not in f:
            print(f"ERROR: --filter expects COL=VALUE, got {f!r}", file=sys.stderr)
            return 2
        col, val = f.split("=", 1)
        if col not in fields:
            print(f"ERROR: --filter column {col!r} not in CSV", file=sys.stderr)
            return 2
        filters.append((col, val))
    rows = apply_filters(rows, filters, msgs)
    try:
        rows = one_per_study(rows, args.one_per_study, msgs)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    if not rows:
        print("ERROR: no rows left after filtering", file=sys.stderr)
        return 2
    if args.subgroup and args.subgroup not in fields:
        print(f"ERROR: --subgroup column {args.subgroup!r} not in CSV", file=sys.stderr)
        return 2
    ps = per_study(rows, cc_all=args.cc_all)
    k = len(ps)
    outdir = os.path.join(args.out, args.name)
    os.makedirs(outdir, exist_ok=True)
    instruments = sorted({d["instrument"] for d in ps})
    refs = sorted({d["reference_standard"] for d in ps})
    if len(instruments) > 1:
        warn(msgs, f"pooling across {len(instruments)} instruments: {instruments}. Make sure this is the intended pooling unit.")
    if len(refs) > 1:
        warn(msgs, f"pooling across {len(refs)} reference standards: {refs}. Consider --subgroup reference_standard or --filter.")
    zero = [d["label"] for d in ps if d["continuity_correction"] > 0]
    if zero:
        warn(msgs, f"0.5 continuity correction applied (LR/DOR/normal-approximation only) to: {zero}")

    uni = univariate_block(ps)
    res = OrderedDict(name=args.name, input=os.path.abspath(args.csv), version=VERSION, k=k,
                      filters=[f"{c}={v}" for c, v in filters], one_per_study=args.one_per_study,
                      instruments=instruments, reference_standards=refs, warnings=msgs)
    res["per_study"] = ps
    res["univariate"] = uni
    title = args.title or f"{args.name} (k = {k})"
    pooled = None
    primary = None
    hs = None
    if k < 4:
        warn(msgs, f"k = {k} < 4: the bivariate random-effects model is not fitted (between-study variances and their "
                   "correlation are not estimable). Reporting per-study estimates and univariate pooling for description only.")
        res["primary_model"] = "none (k < 4)"
        res["pooled"] = None
        res["heterogeneity"] = None
        res["hsroc"] = None
        res["fits"] = {}
    else:
        if k <= 10:
            warn(msgs, f"k = {k} (4-10): bivariate model fitted, but between-study variance and correlation estimates are "
                       "unstable; report the prediction region with caution and consider the normal-approximation REML fit "
                       "and univariate pooling as sensitivity analyses.")
        X = np.ones((k, 1))
        primary, fits = fit_bivariate(ps, X, args.method, msgs, args.quadrature)
        rho_hat = primary["Sigma"][0, 1] / math.sqrt(primary["Sigma"][0, 0] * primary["Sigma"][1, 1])
        if abs(rho_hat) > 0.98:
            warn(msgs, f"between-study correlation is at its boundary (rho = {rho_hat:.2f}). With few studies the "
                       "correlation is poorly identified; the prediction region shape is not trustworthy and the "
                       "HSROC curve is degenerate (sigma^2_alpha or sigma^2_theta ~ 0). Report sens and spec with "
                       "their CIs, not the curve.")
        if primary.get("tau_at_boundary") and any(primary["tau_at_boundary"]):
            warn(msgs, "GLMM: a between-study SD is at its lower bound (≈0); the random effect for that margin is effectively "
                       "absent and the prediction region on that axis equals the confidence region.")
        pooled = summary_block(primary)
        hs = hsroc_from_bivariate(primary["beta"][0], primary["beta"][1], primary["Sigma"])
        res["primary_model"] = primary["method"]
        res["pooled"] = pooled
        res["heterogeneity"] = heterogeneity_block(primary, ps, uni)
        res["hsroc"] = hs
        res["fits"] = OrderedDict((n, fit_to_json(f)) for n, f in fits.items())
        # sanity: bivariate vs univariate DL on logit sens
        diff = abs(pooled["logit_sens"] - uni["sens"]["random"])
        res["sanity_check"] = dict(logit_sens_bivariate=pooled["logit_sens"], logit_sens_univariate_DL=uni["sens"]["random"],
                                   abs_difference=diff)
        if diff > 0.5:
            warn(msgs, f"bivariate and univariate DL pooled logit sensitivity differ by {diff:.2f}; inspect the data "
                       "(strong sens/spec correlation or an outlying study can cause this).")
    res["deeks"] = deeks_test(ps)
    if args.subgroup:
        if k < 4:
            warn(msgs, "--subgroup ignored because k < 4")
            res["subgroup"] = None
        else:
            res["subgroup"] = subgroup_analysis(ps, args.subgroup, args.method, msgs, args.quadrature)
    else:
        res["subgroup"] = None

    # outputs
    plot_sroc(ps, primary, hs, os.path.join(outdir, "sroc"), title,
              uni_point=(uni["sens"]["random_prop"], uni["spec"]["random_prop"]) if primary is None else None)
    plot_forest(ps, pooled if pooled else None, os.path.join(outdir, "forest"), title,
                pooled_label=f"Pooled ({res['primary_model']})")
    with open(os.path.join(outdir, "per_study.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(ps[0].keys()))
        w.writeheader()
        for d in ps:
            w.writerow({k2: (f"{v:.6g}" if isinstance(v, float) else v) for k2, v in d.items()})
    with open(os.path.join(outdir, "results.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=2, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
    with open(os.path.join(outdir, "summary.md"), "w", encoding="utf-8") as fh:
        fh.write(results_to_md(res, args))
    # console summary
    print(f"\n{args.name}: k = {k}; primary model: {res['primary_model']}")
    if pooled:
        print(f"  sensitivity {ci_str(pooled['sens'], pooled['sens_lo'], pooled['sens_hi'])}")
        print(f"  specificity {ci_str(pooled['spec'], pooled['spec_lo'], pooled['spec_hi'])}")
        h = res["heterogeneity"]
        print(f"  tau (logit sens, logit spec) = {h['tau_logit_sens']:.3f}, {h['tau_logit_spec']:.3f}; rho = {h['rho_sens_spec']:.3f}")
        print(f"  DOR {ci_str(pooled['DOR'], pooled['DOR_lo'], pooled['DOR_hi'], 1)}; LR+ {fmt(pooled['LR_pos'], 2)}; LR- {fmt(pooled['LR_neg'], 2)}")
    else:
        print(f"  univariate DL sensitivity {ci_str(uni['sens']['random_prop'], uni['sens']['random_prop_lo'], uni['sens']['random_prop_hi'])}")
        print(f"  univariate DL specificity {ci_str(uni['spec']['random_prop'], uni['spec']['random_prop_lo'], uni['spec']['random_prop_hi'])}")
    if res.get("subgroup"):
        print(f"  subgroup {args.subgroup}: LRT chi2 = {res['subgroup']['LRT']:.2f}, df = {res['subgroup']['df']}, p = {res['subgroup']['p']:.3f}")
    print(f"  {len(msgs)} warning(s); outputs in {outdir}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="dta_pool.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate", help="check a dta.csv and list candidate pooling units")
    v.add_argument("csv")
    r = sub.add_parser("run", help="fit the models and write outputs")
    r.add_argument("csv")
    r.add_argument("--name", required=True, help="analysis name; outputs go to <out>/<name>/")
    r.add_argument("--out", default="analysis/dta", help="output root (default analysis/dta)")
    r.add_argument("--title", default=None, help="figure title (default: name and k)")
    r.add_argument("--method", choices=["auto", "glmm", "reml", "ml"], default="auto",
                   help="primary model: auto = binomial GLMM, falling back to normal-approximation REML (default)")
    r.add_argument("--quadrature", type=int, default=15, help="Gauss-Hermite nodes per dimension for the GLMM (default 15)")
    r.add_argument("--filter", action="append", metavar="COL=VALUE",
                   help="keep rows where COL == VALUE (repeatable; 'COL=' keeps rows where COL is empty)")
    r.add_argument("--label-col", default=None, metavar="COL",
                   help="column to use as the study label in tables and plots (default: 'label', else study_id)")
    r.add_argument("--one-per-study", default=None, metavar="RULE",
                   help="when a study_id has several rows keep one: closest:X (threshold nearest X), youden, largest, first")
    r.add_argument("--subgroup", default=None, metavar="COL", help="bivariate meta-regression on a categorical column with an LRT")
    r.add_argument("--cc-all", action="store_true",
                   help="apply the 0.5 continuity correction to every study when any study has a zero cell (mada default), "
                        "instead of only to studies with a zero cell")
    args = ap.parse_args(argv)
    try:
        return cmd_validate(args) if args.cmd == "validate" else cmd_run(args)
    except KeyboardInterrupt:
        return 1


if __name__ == "__main__":
    sys.exit(main())
