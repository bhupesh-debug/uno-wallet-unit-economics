"""Deterministic LTV / CAC engine for one acquired Uno Wallet user.

Model (closed form, per acquired user):
    LTV = activation x net_rev_per_active_month / (1 - retention x discount_factor)
where discount_factor = 1 / (1 + monthly_discount). All inputs are [ASSUMPTION]s
(see src/data_gen.py); nothing here is a fact about Uno Wallet.

Payback is solved numerically on the cumulative discounted revenue curve.
Break-even retention is the monthly retention at which LTV == CAC, solved
in closed form.
"""
import numpy as np


def ltv_per_acquired(activation, net_rev, retention, discount_monthly=0.01):
    """Expected lifetime value of one acquired user ($)."""
    d = 1.0 / (1.0 + discount_monthly)
    denom = 1.0 - retention * d
    if denom <= 0:
        return float("inf")
    return activation * net_rev / denom


def ltv_per_activated(net_rev, retention, discount_monthly=0.01):
    d = 1.0 / (1.0 + discount_monthly)
    denom = 1.0 - retention * d
    if denom <= 0:
        return float("inf")
    return net_rev / denom


def payback_months(cac_per_acquired, activation, net_rev, retention,
                   discount_monthly=0.01, horizon=60):
    """Months until cumulative expected discounted revenue per acquired user
    reaches CAC. Returns None if never within the horizon."""
    d = 1.0 / (1.0 + discount_monthly)
    cum = 0.0
    for t in range(horizon):
        cum += activation * net_rev * (retention * d) ** t
        if cum >= cac_per_acquired:
            # Linear interpolation inside the month for a fractional answer.
            prev = cum - activation * net_rev * (retention * d) ** t
            frac = (cac_per_acquired - prev) / max(activation * net_rev * (retention * d) ** t, 1e-9)
            return round(t + frac, 1)
    return None


def breakeven_retention(cac_per_acquired, activation, net_rev, discount_monthly=0.01):
    """Monthly retention at which LTV == CAC. Returns None if even retention
    of 1.0 cannot break even (or if CAC is already covered at retention 0)."""
    d = 1.0 / (1.0 + discount_monthly)
    # LTV = activation*net_rev / (1 - r*d) = CAC  =>  r = (1 - activation*net_rev/CAC) / d
    if cac_per_acquired <= 0:
        return 0.0
    r_star = (1.0 - activation * net_rev / cac_per_acquired) / d
    if r_star < 0:
        return 0.0  # breaks even even with zero retention (CAC trivially covered)
    if r_star > 1.0:
        return None  # no retention rate can ever break even
    return round(float(r_star), 3)


def channel_table(channels, net_rev, retention, discount_monthly=0.01):
    """Per-channel LTV, CAC, LTV:CAC, payback and break-even retention."""
    rows = []
    for name, spec in channels.items():
        cac = spec["cac"]
        act = spec["activation"]
        ltv = ltv_per_acquired(act, net_rev, retention, discount_monthly)
        rows.append({
            "channel": name,
            "cac": cac,
            "activation": act,
            "ltv": round(ltv, 2),
            "ltv_cac": round(ltv / cac, 2) if cac else None,
            "payback_months": payback_months(cac, act, net_rev, retention, discount_monthly),
            "breakeven_retention": breakeven_retention(cac, act, net_rev, discount_monthly),
        })
    return rows


def blended(channels, net_rev, retention, discount_monthly=0.01):
    """Mix-weighted blended CAC, activation, LTV, LTV:CAC, payback, break-even."""
    cac = sum(s["mix"] * s["cac"] for s in channels.values())
    act = sum(s["mix"] * s["activation"] for s in channels.values())
    ltv = ltv_per_acquired(act, net_rev, retention, discount_monthly)
    return {
        "cac": round(cac, 2),
        "activation": round(act, 3),
        "ltv": round(ltv, 2),
        "ltv_cac": round(ltv / cac, 2),
        "payback_months": payback_months(cac, act, net_rev, retention, discount_monthly),
        "breakeven_retention": breakeven_retention(cac, act, net_rev, discount_monthly),
    }
