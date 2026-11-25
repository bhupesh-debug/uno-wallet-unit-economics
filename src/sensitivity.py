"""One-at-a-time sensitivity analysis for the LTV:CAC model.

Each driver is perturbed +/-20% from its base [ASSUMPTION] while the others are
held fixed. The ranking answers the honest question: which assumption dominates
the answer, and where is the model fragile? A single-point LTV with no
sensitivity would be a failure — this module is the antidote.
"""
from src.ltv import ltv_per_acquired


def sensitivity(base_params, drivers, deltas=(-0.20, 0.20)):
    """base_params: dict with keys activation, net_rev, retention, cac,
    discount_monthly. drivers: list of param names to perturb.
    Returns rows sorted by |impact on LTV:CAC| descending.

    Retention is a RATE, so a +/-20% relative move (0.82 -> 0.98) is not a
    plausible scenario — it explodes the denominator and would dominate the
    ranking by construction. Rates are perturbed +/-5 percentage points
    instead (0.77 / 0.87); every other driver moves +/-20%. This is labelled
    wherever the table is shown."""
    def ratio(p):
        return ltv_per_acquired(p["activation"], p["net_rev"], p["retention"],
                                p["discount_monthly"]) / p["cac"]

    base_ratio = ratio(base_params)
    rows = []
    for driver in drivers:
        for delta in deltas:
            p = dict(base_params)
            if driver == "retention":
                # Rate: +/-5 percentage points, not +/-20% relative.
                p[driver] = p[driver] + (0.05 if delta > 0 else -0.05)
                label = 5 if delta > 0 else -5
            else:
                p[driver] = p[driver] * (1 + delta)
                label = int(delta * 100)
            r = ratio(p)
            rows.append({
                "driver": driver,
                "delta_pct": label,
                "value": round(p[driver], 4),
                "ltv_cac": round(r, 2),
                "change_pct": round(100 * (r - base_ratio) / base_ratio, 1),
            })
    # Rank drivers by the spread between their -20% and +20% outcomes.
    spread = {}
    for driver in drivers:
        vals = [row["ltv_cac"] for row in rows if row["driver"] == driver]
        spread[driver] = round(max(vals) - min(vals), 2)
    ranking = sorted(spread.items(), key=lambda kv: -kv[1])
    return {"base_ltv_cac": round(base_ratio, 2), "rows": rows,
            "ranking": [{"driver": d, "spread": s} for d, s in ranking]}
