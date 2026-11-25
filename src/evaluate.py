"""Evaluation: honest comparisons and the numbers the report/deck consume.

- Empirical LTV (from the synthetic cohort's actual lifetime revenue) vs the
  closed-form exponential LTV — the gap is reported, not hidden.
- Activation model AUC vs the naive rate baseline (0.500 by construction).
- Channel economics from the deterministic engine.
"""
import numpy as np

from src.ltv import blended, channel_table, ltv_per_acquired
from src.models import activation_model, empirical_retention_curve, fit_exponential_retention
from src.sensitivity import sensitivity


def evaluate(df, channels, net_rev, retention, discount):
    act_model = activation_model(df)
    curve = empirical_retention_curve(df)
    fit = fit_exponential_retention(curve)

    # Empirical LTV per acquired user, straight from the synthetic cohort.
    empirical_ltv = float(df["lifetime_rev"].mean())
    empirical_cac = float(df["cac"].mean())
    closed_ltv = ltv_per_acquired(
        float(df["activated"].mean()), net_rev, retention, discount)
    gap_pct = 100 * (empirical_ltv - closed_ltv) / closed_ltv if closed_ltv else None

    chan = channel_table(channels, net_rev, retention, discount)
    blend = blended(channels, net_rev, retention, discount)
    sens = sensitivity(
        {"activation": blend["activation"], "net_rev": net_rev,
         "retention": retention, "cac": blend["cac"], "discount_monthly": discount},
        drivers=["retention", "net_rev", "cac", "activation", "discount_monthly"])

    # Levers: the three drivers whose favourable move lifts LTV:CAC most
    # (retention moves +5pp, every other driver +20% — see sensitivity.py).
    up = {}
    for r in sens["rows"]:
        if r["delta_pct"] > 0:
            up[r["driver"]] = max(up.get(r["driver"], -1e9), r["change_pct"])
    levers = sorted(up.items(), key=lambda kv: -kv[1])[:3]

    return {
        "n_users": int(len(df)),
        "activation_rate_empirical": round(float(df["activated"].mean()), 3),
        "blended": blend,
        "channels": chan,
        "empirical_ltv_per_acquired": round(empirical_ltv, 2),
        "empirical_cac": round(empirical_cac, 2),
        "empirical_ltv_cac": round(empirical_ltv / empirical_cac, 2),
        "closed_form_ltv": round(closed_ltv, 2),
        "empirical_vs_closed_gap_pct": round(gap_pct, 1),
        "activation_auc": act_model["auc"],
        "activation_baseline_auc": act_model["baseline_auc"],
        "activation_baseline_rate": act_model["baseline_rate"],
        "activation_coefficients": act_model["coefficients"],
        "fitted_retention": fit["retention"],
        "retention_fit_rmse": fit["rmse"],
        "assumed_retention": retention,
        "net_rev_per_active_month": round(net_rev, 2),
        "sensitivity": sens,
        "top_levers": [{"driver": d, "ltv_cac_uplift_pct": c} for d, c in levers],
        "act_model": act_model,
        "retention_curve": curve,
        "retention_fitted": fit["fitted"],
    }
