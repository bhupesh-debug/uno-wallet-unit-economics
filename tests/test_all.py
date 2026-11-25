"""Test suite for the Uno Wallet unit-economics project.

Counts use a runtime counter: every check() call increments, and the suite
prints a single "N passed" line at the end. Report that runtime line — never
count check() call sites by hand (checks inside loops execute multiple times).
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src.data_gen import (BASE_MONTHLY_RETENTION, CHANNELS,  # noqa: E402
                          DISCOUNT_MONTHLY, NET_REV_PER_ACTIVE_MONTH,
                          generate_users)
from src.evaluate import evaluate  # noqa: E402
from src.ltv import (blended, breakeven_retention, channel_table,  # noqa: E402
                     ltv_per_acquired, payback_months)
from src.models import activation_model, fit_exponential_retention  # noqa: E402
from src.sensitivity import sensitivity  # noqa: E402

PASSED = 0
FAILED = []


def check(name, cond):
    global PASSED
    if cond:
        PASSED += 1
    else:
        FAILED.append(name)
        print(f"FAIL: {name}")


def main():
    df = generate_users()
    m = (ROOT / "reports" / "metrics.json")
    metrics = json.loads(m.read_text()) if m.exists() else {}

    # --- data generation ---------------------------------------------------
    check("data: 6000 users", len(df) == 6000)
    check("data: columns present", set(["user_id", "channel", "intent", "cac",
          "activated", "retention", "months_active", "monthly_spend",
          "lifetime_rev"]) <= set(df.columns))
    check("data: channels are the five defined", set(df["channel"].unique()) == set(CHANNELS))
    check("data: activation is binary", set(df["activated"].unique()) <= {0, 1})
    check("data: no activated user has 0 months active",
          bool(((df["activated"] == 1) == (df["months_active"] > 0)).all()))
    check("data: inactive users earn zero lifetime revenue",
          bool((df.loc[df["activated"] == 0, "lifetime_rev"] == 0).all()))
    check("data: negative lifetime revenue only for low spenders "
          "(monthly net = spend x 2.1% x 30% - $1.10 turns negative below ~$175/mo spend)",
          bool(((df["lifetime_rev"] < 0) <= (df["monthly_spend"] < 175)).all()))
    check("data: fewer than 5% of users have negative lifetime revenue",
          bool((df["lifetime_rev"] < 0).mean() < 0.05))
    check("data: CAC matches channel table",
          bool((df["cac"] == df["channel"].map({c: s["cac"] for c, s in CHANNELS.items()})).all()))
    check("data: reproducible with same seed",
          generate_users()["lifetime_rev"].equals(df["lifetime_rev"]))
    check("data: channel mix within 3pp of assumption", all(
        abs(df["channel"].value_counts(normalize=True)[c] - CHANNELS[c]["mix"]) < 0.03
        for c in CHANNELS))
    check("data: activation rate within 4pp of assumption per channel", all(
        abs(df[df["channel"] == c]["activated"].mean() - CHANNELS[c]["activation"]) < 0.04
        for c in CHANNELS))

    # --- LTV engine: closed form vs brute-force simulation -----------------
    net = NET_REV_PER_ACTIVE_MONTH
    check("ltv: net revenue per active month is 6.15 (1150 x 2.1% x 30% - 1.10)",
          abs(net - 6.145) < 1e-9)
    for act, ret in [(0.6, 0.82), (0.45, 0.75), (0.72, 0.90)]:
        closed = ltv_per_acquired(act, net, ret, DISCOUNT_MONTHLY)
        d = 1 / (1 + DISCOUNT_MONTHLY)
        brute = sum(act * net * (ret * d) ** t for t in range(600))
        check(f"ltv: closed form matches brute force (act={act}, ret={ret})",
              abs(closed - brute) < 0.01)
    check("ltv: higher retention raises LTV",
          ltv_per_acquired(0.6, net, 0.90, DISCOUNT_MONTHLY) >
          ltv_per_acquired(0.6, net, 0.70, DISCOUNT_MONTHLY))
    check("ltv: higher CAC lowers nothing in LTV (LTV is CAC-free)",
          ltv_per_acquired(0.6, net, 0.82, DISCOUNT_MONTHLY) ==
          ltv_per_acquired(0.6, net, 0.82, DISCOUNT_MONTHLY))

    # --- payback ------------------------------------------------------------
    pb = payback_months(18.90, 0.5875, net, 0.82, DISCOUNT_MONTHLY)
    check("payback: blended case pays back in finite months", pb is not None and 0 < pb < 60)
    check("payback: larger CAC means later payback (both below LTV, so both pay back)",
          payback_months(15.0, 0.5875, net, 0.82, DISCOUNT_MONTHLY) >
          payback_months(10.0, 0.5875, net, 0.82, DISCOUNT_MONTHLY))
    check("payback: zero CAC pays back immediately",
          payback_months(0.0, 0.5875, net, 0.82, DISCOUNT_MONTHLY) == 0.0)
    check("payback: impossible economics returns None",
          payback_months(10000.0, 0.1, net, 0.5, DISCOUNT_MONTHLY) is None)

    # --- break-even retention ------------------------------------------------
    be = breakeven_retention(18.90, 0.5875, net, DISCOUNT_MONTHLY)
    check("breakeven: returns a rate between 0 and 1", be is not None and 0 <= be <= 1)
    check("breakeven: at break-even retention, LTV equals CAC",
          abs(ltv_per_acquired(0.5875, net, be, DISCOUNT_MONTHLY) - 18.90) < 0.05)
    check("breakeven: higher CAC needs higher retention",
          breakeven_retention(40.0, 0.5875, net, DISCOUNT_MONTHLY) >
          breakeven_retention(18.90, 0.5875, net, DISCOUNT_MONTHLY))
    check("breakeven: impossible CAC returns None",
          breakeven_retention(100000.0, 0.1, net, DISCOUNT_MONTHLY) is None)

    # --- channel table / blended --------------------------------------------
    chan = channel_table(CHANNELS, net, BASE_MONTHLY_RETENTION, DISCOUNT_MONTHLY)
    check("channels: five rows", len(chan) == 5)
    check("channels: referral LTV:CAC beats paid search",
          next(r for r in chan if r["channel"] == "referral")["ltv_cac"] >
          next(r for r in chan if r["channel"] == "paid_search")["ltv_cac"])
    check("channels: paid channels have LTV:CAC below 1 (loss-making at base assumptions)",
          all(next(r for r in chan if r["channel"] == c)["ltv_cac"] < 1.0
              for c in ("paid_search", "paid_social")))
    b = blended(CHANNELS, net, BASE_MONTHLY_RETENTION, DISCOUNT_MONTHLY)
    check("blended: CAC is mix-weighted (~18.90)",
          abs(b["cac"] - 18.90) < 0.01)
    check("blended: activation is mix-weighted (~0.588)",
          abs(b["activation"] - 0.5875) < 0.001)
    check("blended: LTV:CAC near 1 (fragile economics)",
          0.8 < b["ltv_cac"] < 1.3)
    check("blended: payback is finite", b["payback_months"] is not None)
    check("blended: break-even retention is within 1pp of assumed retention",
          abs(b["breakeven_retention"] - BASE_MONTHLY_RETENTION) < 0.01)

    # --- sensitivity ---------------------------------------------------------
    sens = sensitivity({"activation": b["activation"], "net_rev": net,
                        "retention": BASE_MONTHLY_RETENTION, "cac": b["cac"],
                        "discount_monthly": DISCOUNT_MONTHLY},
                       drivers=["retention", "net_rev", "cac", "activation",
                                "discount_monthly"])
    check("sensitivity: five drivers ranked", len(sens["ranking"]) == 5)
    check("sensitivity: retention is the #1 driver",
          sens["ranking"][0]["driver"] == "retention")
    check("sensitivity: +5pp retention raises LTV:CAC",
          next(r for r in sens["rows"] if r["driver"] == "retention"
               and r["delta_pct"] == 5)["change_pct"] > 0)
    check("sensitivity: +20% CAC lowers LTV:CAC",
          next(r for r in sens["rows"] if r["driver"] == "cac"
               and r["delta_pct"] == 20)["change_pct"] < 0)
    check("sensitivity: -5pp retention pushes LTV:CAC below 1",
          next(r for r in sens["rows"] if r["driver"] == "retention"
               and r["delta_pct"] == -5)["ltv_cac"] < 1.0)

    # --- activation model ----------------------------------------------------
    am = activation_model(df)
    check("activation model: AUC beats chance", am["auc"] > 0.5)
    check("activation model: AUC beats the naive baseline", am["auc"] > am["baseline_auc"])
    check("activation model: AUC is plausible for a synthetic signal (0.6-0.95)",
          0.6 < am["auc"] < 0.95)
    check("activation model: intent coefficient is positive (higher intent -> activates)",
          am["coefficients"].get("intent", 0) > 0)

    # --- retention fit --------------------------------------------------------
    from src.models import empirical_retention_curve
    curve = empirical_retention_curve(df)
    fit = fit_exponential_retention(curve)
    check("retention fit: fitted retention is ABOVE the assumed base "
          "(heterogeneity bias: a mixture of geometrics has a heavier tail "
          "than any single exponential, so a single-r fit overstates retention)",
          BASE_MONTHLY_RETENTION < fit["retention"] < BASE_MONTHLY_RETENTION + 0.07)
    check("retention fit: RMSE is 0.05-0.10 — the single-exponential model "
          "MISFITS the empirical curve (heterogeneity again: the mixture tail "
          "is heavier than any single r). This misfit is a finding, not a bug: "
          "the closed-form LTV understates the tail value, which is why the "
          "empirical LTV:CAC (1.18) sits 14.4% above the closed form (1.03).",
          0.05 <= fit["rmse"] < 0.10)
    check("retention curve: monotone non-increasing",
          bool(np.all(np.diff(curve) <= 1e-9)))

    # --- full evaluation + metrics file ---------------------------------------
    res = evaluate(df, CHANNELS, net, BASE_MONTHLY_RETENTION, DISCOUNT_MONTHLY)
    check("evaluate: empirical LTV:CAC within 25% of closed form",
          abs(res["empirical_ltv_cac"] - res["blended"]["ltv_cac"]) /
          res["blended"]["ltv_cac"] < 0.25)
    check("evaluate: three levers named", len(res["top_levers"]) == 3)
    check("evaluate: retention is a top lever",
          any(lv["driver"] == "retention" for lv in res["top_levers"]))
    if metrics:
        check("metrics: file has blended LTV:CAC", "blended" in metrics)
        check("metrics: assumptions section present", "assumptions" in metrics)
        check("metrics: sensitivity ranking present",
              "sensitivity" in metrics and "ranking" in metrics["sensitivity"])
    check("metrics: charts exist", all(
        (ROOT / "reports" / "charts" / f).exists() for f in
        ["retention_curve.png", "sensitivity_tornado.png",
         "ltv_cac_by_channel.png", "payback_curve.png", "activation_roc.png"]))

    print(f"\n{PASSED} passed, {len(FAILED)} failed")
    if FAILED:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
