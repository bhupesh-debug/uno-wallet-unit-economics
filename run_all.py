"""Run the full pipeline: synthetic data -> LTV/CAC engine -> sensitivity ->
activation model + retention fit -> charts -> reports/metrics.json.

Usage: python run_all.py  (from the project root, or any cwd)
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src import charts  # noqa: E402
from src.data_gen import (BASE_MONTHLY_RETENTION, CHANNELS, DISCOUNT_MONTHLY,
                          NET_REV_PER_ACTIVE_MONTH, generate_users)  # noqa: E402
from src.evaluate import evaluate  # noqa: E402


def main():
    df = generate_users()
    df.to_csv(ROOT / "data" / "synthetic" / "users.csv", index=False)
    res = evaluate(df, CHANNELS, NET_REV_PER_ACTIVE_MONTH,
                   BASE_MONTHLY_RETENTION, DISCOUNT_MONTHLY)

    chart_dir = ROOT / "reports" / "charts"
    chart_dir.mkdir(parents=True, exist_ok=True)
    charts.retention_curve(res["retention_curve"], res["retention_fitted"],
                           chart_dir / "retention_curve.png")
    charts.tornado(res["sensitivity"]["rows"], res["sensitivity"]["base_ltv_cac"],
                   chart_dir / "sensitivity_tornado.png")
    charts.ltv_cac_by_channel(res["channels"], chart_dir / "ltv_cac_by_channel.png")
    charts.payback_curve(res["blended"]["cac"], res["blended"]["activation"],
                         NET_REV_PER_ACTIVE_MONTH, BASE_MONTHLY_RETENTION,
                         DISCOUNT_MONTHLY, res["blended"]["payback_months"],
                         chart_dir / "payback_curve.png")
    charts.roc_curve_chart(res["act_model"]["y_test"], res["act_model"]["proba_test"],
                           res["activation_auc"], chart_dir / "activation_roc.png")

    metrics = {k: v for k, v in res.items()
               if k not in ("act_model", "retention_curve", "retention_fitted")}
    metrics["assumptions"] = {
        "channels": {c: {"mix": s["mix"], "cac": s["cac"], "activation": s["activation"]}
                     for c, s in CHANNELS.items()},
        "base_monthly_retention": BASE_MONTHLY_RETENTION,
        "mean_monthly_spend": 1150.0,
        "earn_rate": 0.021,
        "uno_take": 0.30,
        "servicing_cost_per_active_month": 1.10,
        "discount_monthly": DISCOUNT_MONTHLY,
        "note": "ALL inputs are [ASSUMPTION]s, not Uno Wallet facts. "
                "No Uno Wallet financial data is public.",
    }
    (ROOT / "reports" / "metrics.json").write_text(json.dumps(metrics, indent=2))

    print("users:", res["n_users"])
    print("blended LTV:CAC:", res["blended"]["ltv_cac"],
          "| LTV $", res["blended"]["ltv"], "| CAC $", res["blended"]["cac"])
    print("payback (months):", res["blended"]["payback_months"])
    print("break-even retention:", res["blended"]["breakeven_retention"],
          "| assumed retention:", res["assumed_retention"])
    print("empirical LTV:CAC:", res["empirical_ltv_cac"],
          "| closed-form LTV:CAC:", round(res["closed_form_ltv"] / res["empirical_cac"], 2),
          "| gap:", res["empirical_vs_closed_gap_pct"], "%")
    print("activation AUC:", res["activation_auc"], "vs baseline", res["activation_baseline_auc"])
    print("fitted retention:", res["fitted_retention"], "| assumed:", res["assumed_retention"])
    print("sensitivity ranking:", [r["driver"] for r in res["sensitivity"]["ranking"]])
    print("top levers:", res["top_levers"])


if __name__ == "__main__":
    main()
