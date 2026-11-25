"""Charts for the unit-economics project (matplotlib, saved as PNGs)."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve

NAVY = "#1A3A6B"
GREEN = "#2E7D5B"
RED = "#B03A2E"
AMBER = "#D98E04"
GREY = "#555555"


def _save(fig, path):
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def retention_curve(empirical, fitted, path):
    fig, ax = plt.subplots(figsize=(7, 4))
    t = np.arange(len(empirical))
    ax.plot(t, empirical, label="Empirical cohort (synthetic)", color=NAVY, lw=2)
    ax.plot(t, fitted, label="Exponential fit", color=AMBER, lw=2, ls="--")
    ax.set_xlabel("Months since activation")
    ax.set_ylabel("Share of activated users still active")
    ax.set_title("Cohort retention: empirical vs exponential fit")
    ax.legend()
    ax.grid(alpha=0.3)
    _save(fig, path)


def tornado(rows, base_ratio, path):
    """rows: sensitivity rows; one bar per driver showing -20% / +20% outcomes."""
    drivers = []
    lo, hi = [], []
    for driver in dict.fromkeys(r["driver"] for r in rows):
        vals = sorted((r["delta_pct"], r["ltv_cac"]) for r in rows if r["driver"] == driver)
        drivers.append(driver)
        lo.append(vals[0][1])   # most negative perturbation
        hi.append(vals[-1][1])  # most positive perturbation
    order = np.argsort([h - l for h, l in zip(hi, lo)])[::-1]
    drivers = [drivers[i] for i in order]
    lo = [lo[i] for i in order]
    hi = [hi[i] for i in order]
    fig, ax = plt.subplots(figsize=(7, 4.2))
    y = np.arange(len(drivers))
    ax.barh(y, np.array(hi) - base_ratio, left=base_ratio, color=GREEN, height=0.55, label="+20% driver")
    ax.barh(y, np.array(lo) - base_ratio, left=base_ratio, color=RED, height=0.55, label="-20% driver")
    ax.axvline(base_ratio, color=NAVY, lw=2, ls="--")
    ax.axvline(1.0, color=GREY, lw=1, ls=":")
    ax.set_yticks(y)
    ax.set_yticklabels(drivers)
    ax.set_xlabel("LTV : CAC")
    ax.set_title(f"Sensitivity tornado — base LTV:CAC {base_ratio:.2f} (dotted line = 1.0 break-even)")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3, axis="x")
    _save(fig, path)


def ltv_cac_by_channel(table, path):
    names = [r["channel"] for r in table]
    ltv = [r["ltv"] for r in table]
    cac = [r["cac"] for r in table]
    x = np.arange(len(names))
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(x - 0.2, ltv, 0.4, label="LTV per acquired user ($)", color=GREEN)
    ax.bar(x + 0.2, cac, 0.4, label="CAC per acquired user ($)", color=RED)
    ax.set_xticks(x)
    ax.set_xticklabels(names)
    ax.set_ylabel("$ per acquired user")
    ax.set_title("LTV vs CAC by acquisition channel (synthetic, [ASSUMPTION] inputs)")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3, axis="y")
    _save(fig, path)


def payback_curve(cac, activation, net_rev, retention, discount, payback, path):
    d = 1.0 / (1.0 + discount)
    months = np.arange(0, 37)
    cum = np.array([activation * net_rev * sum((retention * d) ** t for t in range(m + 1))
                    for m in months])
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(months, cum, color=NAVY, lw=2, label="Cumulative expected revenue / acquired user")
    ax.axhline(cac, color=RED, lw=2, ls="--", label=f"Blended CAC ${cac:.2f}")
    if payback:
        ax.axvline(payback, color=AMBER, lw=2, ls=":")
        ax.annotate(f"Payback ~{payback:.1f} mo", (payback, cac),
                    textcoords="offset points", xytext=(8, 8), fontsize=9)
    ax.set_xlabel("Months since acquisition")
    ax.set_ylabel("Cumulative discounted revenue ($)")
    ax.set_title("Payback: cumulative revenue vs blended CAC")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    _save(fig, path)


def roc_curve_chart(y_test, proba, auc, path):
    fpr, tpr, _ = roc_curve(y_test, proba)
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.plot(fpr, tpr, color=NAVY, lw=2, label=f"Logistic regression (AUC {auc:.3f})")
    ax.plot([0, 1], [0, 1], color=GREY, ls="--", label="Chance (AUC 0.500)")
    ax.set_xlabel("False positive rate")
    ax.set_ylabel("True positive rate")
    ax.set_title("Activation prediction — ROC")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    _save(fig, path)
