#!/usr/bin/env python3
"""Parameter-recovery check for dta_pool.py: simulate from known bivariate parameters and refit.

Prints, for each seed, the GLMM and normal-approximation (REML) estimates next to the truth,
then the mean bias and the coverage of the 95% CIs for pooled sensitivity and specificity.
Used to produce references/validation.md; re-run it after changing the fitting code.
"""
import argparse
import math
import os
import sys

try:
    import numpy as np
except ImportError:  # python3 -I hides the user site; re-add that one trusted dir
    import site
    sys.path.append(site.getusersitepackages())
    try:
        import numpy as np
    except ImportError:
        sys.exit("numpy/scipy/matplotlib are required: python3 -m pip install --user --break-system-packages numpy scipy matplotlib")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # the skill's own folder, not untrusted input
import dta_pool as dp  # noqa: E402


def simulate(rng, k, mu, Sigma, n1r, n0r):
    rows = []
    for i in range(k):
        u = rng.multivariate_normal(mu, Sigma)
        s, c = dp.expit(u[0]), dp.expit(u[1])
        n1, n0 = int(rng.integers(*n1r)), int(rng.integers(*n0r))
        tp, tn = int(rng.binomial(n1, s)), int(rng.binomial(n0, c))
        rows.append(dict(study_id=f"S{i}", label=f"S{i}", instrument="sim", threshold="1", reference_standard="sim",
                         TP=tp, FP=n0 - tn, FN=n1 - tp, TN=tn))
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--k", type=int, default=30)
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--mu-sens", type=float, default=1.5)
    ap.add_argument("--mu-spec", type=float, default=2.0)
    ap.add_argument("--sd-sens", type=float, default=0.5)
    ap.add_argument("--sd-spec", type=float, default=0.6)
    ap.add_argument("--rho", type=float, default=-0.4)
    ap.add_argument("--quadrature", type=int, default=15)
    a = ap.parse_args(argv)
    mu = np.array([a.mu_sens, a.mu_spec])
    Sigma = np.array([[a.sd_sens ** 2, a.rho * a.sd_sens * a.sd_spec], [a.rho * a.sd_sens * a.sd_spec, a.sd_spec ** 2]])
    truth = dict(sens=float(dp.expit(mu[0])), spec=float(dp.expit(mu[1])), tau_sens=a.sd_sens, tau_spec=a.sd_spec, rho=a.rho)
    print(f"truth: sens {truth['sens']:.4f} spec {truth['spec']:.4f} tau {a.sd_sens} {a.sd_spec} rho {a.rho}; k = {a.k}, {a.seeds} seeds")
    print(f"{'seed':>4s} {'model':10s} {'sens':>7s} {'spec':>7s} {'tau_s':>6s} {'tau_c':>6s} {'rho':>6s}  cover(sens,spec)")
    rec = {m: [] for m in ("GLMM", "REML")}
    for seed in range(1, a.seeds + 1):
        rng = np.random.default_rng(seed)
        ps = dp.per_study(simulate(rng, a.k, mu, Sigma, (20, 151), (40, 401)))
        X = np.ones((a.k, 1))
        fits = {"REML": dp.fit_normal(ps, X, reml=True)}
        start = np.concatenate([fits["REML"]["beta"], fits["REML"]["phi"]])
        fits["GLMM"] = dp.fit_glmm(ps, X, start=start, Q=a.quadrature)
        for m, f in fits.items():
            s = dp.summary_block(f)
            S = f["Sigma"]
            t1, t2 = math.sqrt(S[0, 0]), math.sqrt(S[1, 1])
            rho = S[0, 1] / (t1 * t2)
            cov = (s["sens_lo"] <= truth["sens"] <= s["sens_hi"], s["spec_lo"] <= truth["spec"] <= s["spec_hi"])
            rec[m].append((s["sens"], s["spec"], t1, t2, rho, cov[0], cov[1]))
            print(f"{seed:4d} {m:10s} {s['sens']:7.4f} {s['spec']:7.4f} {t1:6.3f} {t2:6.3f} {rho:6.3f}  {cov}")
    print()
    for m, r in rec.items():
        arr = np.array(r, float)
        print(f"{m}: mean sens {arr[:,0].mean():.4f} (bias {arr[:,0].mean()-truth['sens']:+.4f}), mean spec {arr[:,1].mean():.4f} "
              f"(bias {arr[:,1].mean()-truth['spec']:+.4f}), mean tau {arr[:,2].mean():.3f}/{arr[:,3].mean():.3f}, mean rho {arr[:,4].mean():.3f}, "
              f"CI coverage sens {arr[:,5].mean():.2f} spec {arr[:,6].mean():.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
