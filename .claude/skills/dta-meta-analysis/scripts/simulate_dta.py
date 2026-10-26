#!/usr/bin/env python3
"""Simulate a dta.csv from known bivariate parameters (for validating dta_pool.py).

Study-level logit sensitivity and logit specificity are drawn from a bivariate normal
with means (--mu-sens, --mu-spec), SDs (--sd-sens, --sd-spec) and correlation --rho;
TP ~ Binomial(n_diseased, sens), TN ~ Binomial(n_nondiseased, spec). Group sizes are
drawn uniformly from the given ranges. Deterministic for a given --seed.
"""
import argparse
import csv
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


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--k", type=int, default=30, help="number of studies (default 30)")
    ap.add_argument("--mu-sens", type=float, default=1.5, help="mean logit sensitivity (default 1.5 -> 0.818)")
    ap.add_argument("--mu-spec", type=float, default=2.0, help="mean logit specificity (default 2.0 -> 0.881)")
    ap.add_argument("--sd-sens", type=float, default=0.5)
    ap.add_argument("--sd-spec", type=float, default=0.6)
    ap.add_argument("--rho", type=float, default=-0.4, help="correlation of logit sens and logit spec (default -0.4)")
    ap.add_argument("--n-diseased", default="20:150", help="range min:max (default 20:150)")
    ap.add_argument("--n-nondiseased", default="40:400", help="range min:max (default 40:400)")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--instrument", default="SimQ")
    ap.add_argument("--reference-standard", default="simulated")
    ap.add_argument("--group-col", default=None, help="optional covariate column name; studies alternate A/B with --group-shift on logit sens")
    ap.add_argument("--group-shift", type=float, default=0.0)
    ap.add_argument("--out", required=True, help="output CSV path")
    a = ap.parse_args(argv)
    rng = np.random.default_rng(a.seed)
    cov = np.array([[a.sd_sens ** 2, a.rho * a.sd_sens * a.sd_spec], [a.rho * a.sd_sens * a.sd_spec, a.sd_spec ** 2]])
    lo1, hi1 = (int(x) for x in a.n_diseased.split(":"))
    lo0, hi0 = (int(x) for x in a.n_nondiseased.split(":"))
    rows = []
    for i in range(a.k):
        grp = "A" if i % 2 == 0 else "B"
        shift = a.group_shift if (a.group_col and grp == "B") else 0.0
        u = rng.multivariate_normal([a.mu_sens + shift, a.mu_spec], cov)
        sens, spec = 1 / (1 + np.exp(-u[0])), 1 / (1 + np.exp(-u[1]))
        n1, n0 = int(rng.integers(lo1, hi1 + 1)), int(rng.integers(lo0, hi0 + 1))
        tp, tn = int(rng.binomial(n1, sens)), int(rng.binomial(n0, spec))
        row = dict(study_id=f"S{i + 1:02d}", label=f"Study {i + 1}", instrument=a.instrument, threshold="1",
                   reference_standard=a.reference_standard, TP=tp, FP=n0 - tn, FN=n1 - tp, TN=tn)
        if a.group_col:
            row[a.group_col] = grp
        rows.append(row)
    with open(a.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} studies to {a.out} (true sens {1/(1+np.exp(-a.mu_sens)):.3f}, spec {1/(1+np.exp(-a.mu_spec)):.3f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
