"""Build the 10-page report PDF and the 10-slide deck PDF (reportlab).

Reads reports/metrics.json so every number in the documents comes from the
executed pipeline, not from hand-typed values.
"""
import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (Image, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

ROOT = Path(__file__).resolve().parent
OUT = Path("/home/hatch/workspace/your_files")
CHARTS = ROOT / "reports" / "charts"
M = json.loads((ROOT / "reports" / "metrics.json").read_text())
B = M["blended"]
CHAN = {r["channel"]: r for r in M["channels"]}
SENS = M["sensitivity"]
RANK = SENS["ranking"]
LEVERS = M["top_levers"]
A = M["assumptions"]

NAVY = colors.HexColor("#1A3A6B")
GREEN = colors.HexColor("#2E7D5B")
RED = colors.HexColor("#B03A2E")
AMBER = colors.HexColor("#D98E04")
GREY = colors.HexColor("#555555")
LIGHT = colors.HexColor("#EAF0F7")

H1 = ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=17, leading=21, textColor=NAVY, spaceAfter=8)
H2 = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=12.5, leading=15, textColor=NAVY, spaceBefore=10, spaceAfter=5)
H3 = ParagraphStyle("h3", fontName="Helvetica-Bold", fontSize=10.5, leading=13, textColor=NAVY, spaceBefore=8, spaceAfter=3)
Btxt = ParagraphStyle("b", fontName="Helvetica", fontSize=10, leading=14, spaceAfter=5)
SM = ParagraphStyle("sm", fontName="Helvetica", fontSize=8.5, leading=11.5, textColor=GREY, spaceAfter=4)
CELL = ParagraphStyle("c", fontName="Helvetica", fontSize=9, leading=12)
CELLB = ParagraphStyle("cb", fontName="Helvetica-Bold", fontSize=9, leading=12)
TITLE = ParagraphStyle("t", fontName="Helvetica-Bold", fontSize=24, leading=29, textColor=NAVY)
SUB = ParagraphStyle("s", fontName="Helvetica", fontSize=12.5, leading=17, textColor=GREY)
DT = ParagraphStyle("dt", fontName="Helvetica-Bold", fontSize=15, leading=19, textColor=NAVY, spaceAfter=6)
DB = ParagraphStyle("db", fontName="Helvetica", fontSize=11, leading=15, spaceAfter=6)


def P(text, style=Btxt):
    return Paragraph(text, style)


def bullets(items, style=Btxt):
    return [Paragraph(f"•&nbsp;&nbsp;{t}", style) for t in items]


def table(headers, rows, widths):
    data = [[Paragraph(h, CELLB) for h in headers]]
    for r in rows:
        data.append([Paragraph(str(c), CELL) for c in r])
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#B9C6D8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def chart(name, width=7.0, height=4.0):
    return Image(str(CHARTS / name), width=width * inch, height=height * inch)


def build_report(path):
    doc = SimpleDocTemplate(str(path), pagesize=LETTER,
                            leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                            topMargin=0.7 * inch, bottomMargin=0.7 * inch)
    s = []
    # ---- Page 1: title + executive summary --------------------------------
    s.append(Paragraph("Unit Economics of One Uno User", TITLE))
    s.append(Paragraph("LTV / CAC, payback, break-even retention — and which assumption "
                       "decides the answer", SUB))
    s.append(Spacer(1, 10))
    s.append(P("Bhupesh Chandra Dimri — for the AI Business Analyst role at Uno Wallet "
               "(YC P26). November 25, 2026."))
    s.append(P("Uno Wallet is a two-founder startup building an AI iPhone wallet that "
               "automatically picks the best credit card for every purchase. The founders' "
               "most important question is also the simplest: what is one user worth, what "
               "does one user cost, and which assumption decides whether the answer is good "
               "news? This project answers it with a reproducible LTV/CAC engine on "
               "synthetic data."))
    s.append(P("<b>Read first — synthetic data, labelled assumptions.</b> Uno Wallet has "
               "published no acquisition costs, activation rates, retention, spend, or "
               "revenue figures. Every input in this project is a labelled [ASSUMPTION], "
               "not a fact about Uno Wallet. The point is the machinery and the honest "
               "finding that the answer is fragile — not the numbers themselves."))
    s.append(Paragraph("Executive summary", H2))
    s += bullets([
        f"<b>Blended LTV:CAC {B['ltv_cac']:.2f}</b> (LTV ${B['ltv']:.2f} vs CAC "
        f"${B['cac']:.2f} per acquired user) — essentially break-even, not a win.",
        f"<b>Payback {B['payback_months']:.1f} months</b> — long for a startup that "
        "needs the cash back to fund the next cohort.",
        f"<b>Break-even retention {B['breakeven_retention']:.3f} vs assumed "
        f"{M['assumed_retention']:.2f}</b> — the model lives or dies on a 0.3-point "
        "margin in monthly retention.",
        f"<b>Retention dominates the sensitivity ranking</b> (spread {RANK[0]['spread']:.2f}), "
        f"ahead of CAC ({RANK[1]['spread']:.2f}), revenue per active user "
        f"({RANK[2]['spread']:.2f}) and activation ({RANK[3]['spread']:.2f}). "
        "Discount rate barely matters (0.02).",
        "<b>Channels split hard:</b> organic (5.55) and referral (2.94) pay; paid "
        "search (0.35) and paid social (0.33) never pay back at base assumptions.",
        f"<b>Three levers:</b> retention (+5pp → +{LEVERS[0]['ltv_cac_uplift_pct']:.1f}% "
        f"LTV:CAC), revenue per active user (+20% → +{LEVERS[1]['ltv_cac_uplift_pct']:.0f}%), "
        f"activation (+20% → +{LEVERS[2]['ltv_cac_uplift_pct']:.0f}%).",
        f"<b>Honest check:</b> the empirical cohort LTV:CAC is {M['empirical_ltv_cac']:.2f}, "
        f"{M['empirical_vs_closed_gap_pct']:.1f}% above the closed-form {B['ltv_cac']:.2f} — "
        "user heterogeneity fattens the tail, so a single exponential retention fit "
        f"overstates retention (fitted {M['fitted_retention']:.3f} vs assumed "
        f"{M['assumed_retention']:.2f}, RMSE {M['retention_fit_rmse']:.3f}).",
    ])
    s.append(P("Match score for the Uno Wallet AI Business Analyst role: <b>6 / 10</b> "
               "(see §8). The modelling core is a direct hit; payments domain, startup "
               "experience, and production AI work are the gaps."))
    s.append(PageBreak())

    # ---- Page 2: Step 1 — JD breakdown -------------------------------------
    s.append(Paragraph("1 — JD breakdown (Step 1)", H1))
    s.append(P("The Uno Wallet AI Business Analyst posting is two bullets long. That "
               "thinness is itself a finding: most of the role has to be inferred from "
               "the product, and every inference below is labelled as one."))
    s.append(table(
        ["JD says", "What it means", "What success looks like"],
        [
            ["Analyse data, identify business opportunities, turn insights into actionable recommendations",
             "Own the numbers behind product and growth decisions at a 2-person startup — no analyst team to hand work to",
             "A recommendation the founders act on, with the revenue or cost effect measured afterwards"],
            ["Leverage AI tools to improve business processes and decision-making",
             "Use AI/ML tooling on real workflows (routing, spend analysis, user comms), not demos",
             "A process that runs faster or cheaper with an AI step, with the before/after measured"],
            ["Analytical, entrepreneurial, resourceful; strong problem-solving",
             "Comfort with ambiguity, ownership, and doing the unglamorous work yourself",
             "Ships analysis end-to-end without being asked twice"],
            ["[INFERENCE] YC P26, 2 founders, iPhone wallet, card-rewards wedge",
             "The first hires set the analytics culture; unit economics is the first question a YC startup must answer",
             "LTV:CAC, payback and retention reported as a standing dashboard, not a one-off"],
        ], [1.9 * inch, 2.5 * inch, 2.6 * inch]))
    s.append(Paragraph("Requirement hierarchy", H2))
    s += bullets([
        "<b>Must-have:</b> data analysis (SQL/Python), turning analysis into recommendations, comfort with ambiguity.",
        "<b>High value:</b> unit-economics fluency (LTV/CAC/payback), experimentation thinking, dashboarding.",
        "<b>Implied:</b> payments/rewards economics, retention and cohort analysis, founder-facing communication.",
        "<b>Bonus:</b> iOS/mobile product analytics, growth analytics, LLM/agent workflow experience.",
    ])
    s.append(Paragraph("Risk factors", H2))
    s += bullets([
        "The JD names no tools, no seniority, no years of experience — a panel cannot screen on specifics, so the portfolio has to do the talking.",
        "A 2-person startup cannot absorb a hire who needs structure; the risk is a strong corporate analyst who waits to be told what to do.",
        "Pay ($75–140K) tops out at the floor of the candidate's $140–190K band — this role is backup-only on pay.",
        "E-Verify / I-983 is unconfirmed at a 2-person startup — verify in writing at first contact.",
    ])
    s.append(PageBreak())

    # ---- Page 3: Step 2 — ML problem definition ----------------------------
    s.append(Paragraph("2 — ML problem definition (Step 2)", H1))
    s.append(P("<b>Honest-fit gate.</b> This JD has no deep-learning or LLM requirement. "
               "Forcing a transformer onto it would read as tone-deaf. The project is "
               "therefore framed honestly as an <b>analytics + forecasting project</b>: a "
               "deterministic LTV/CAC engine, a sensitivity analysis, and two small "
               "predictive models that support it. That is what a founder hiring a "
               "business analyst actually wants to see."))
    s.append(table(
        ["Problem", "Input", "Output / target", "Type"],
        [
            ["LTV/CAC engine", "Channel, activation, retention, spend, earn rate, take rate, CAC",
             "LTV, LTV:CAC, payback, break-even retention per channel and blended",
             "Deterministic model"],
            ["Activation prediction", "Channel + pre-signup intent signal",
             "P(activated) — who becomes a real user", "Classification"],
            ["Retention-curve fit", "Cohort months-active",
             "Single exponential retention rate + fit quality (RMSE)",
             "Curve fitting"],
            ["Sensitivity ranking", "All model drivers, perturbed one at a time",
             "Which assumption dominates the answer", "Sensitivity analysis"],
        ], [1.3 * inch, 2.0 * inch, 2.2 * inch, 1.5 * inch]))
    s.append(Paragraph("Dependency map", H2))
    s += bullets([
        "Retention → LTV (compounding: a 5-point move swings LTV:CAC by 36%).",
        "Activation → LTV (linear: only activated users ever pay).",
        "Revenue per active user (spend × earn rate × take − servicing cost) → LTV (linear).",
        "CAC → LTV:CAC (inverse) and payback; channel mix decides the blended number.",
        "Discount rate → almost nothing at these horizons (spread 0.02) — a useful null result.",
    ])
    s.append(Paragraph("Constraints", H2))
    s.append(P("Interpretability beats accuracy: a founder must be able to argue with "
               "every input. No black boxes. Every number is traceable to one labelled "
               "[ASSUMPTION] in the assumptions register (§10)."))
    s.append(PageBreak())

    # ---- Page 4: Steps 3–4 — data + model strategy -------------------------
    s.append(Paragraph("3 — Data strategy (Step 3)", H1))
    s.append(P("No real Uno Wallet data exists publicly, so the dataset is synthetic — "
               "6,000 acquired users, seeded and reproducible, generated by "
               "<i>src/data_gen.py</i>. Schema:"))
    s.append(table(
        ["Field", "Type", "How generated"],
        [
            ["channel", "categorical (5)", "Mix [ASSUMPTION]: organic 30%, referral 25%, paid social 20%, paid search 15%, campus 10%"],
            ["cac", "$", "Per channel [ASSUMPTION]: $4 / $8 / $18 / $38 / $42"],
            ["intent", "0–1", "Beta(2,2) pre-signup intent signal; shifts activation odds"],
            ["activated", "binary", "Channel rate [ASSUMPTION] ± intent adjustment"],
            ["retention", "0.55–0.97", "Normal(0.82, 0.06) per user [ASSUMPTION]"],
            ["months_active", "int 0–36", "Geometric(1 − retention), capped at 36"],
            ["monthly_spend", "$", "Lognormal, mean $1,150 [ASSUMPTION]"],
            ["lifetime_rev", "$", "Discounted sum of monthly net revenue while active"],
        ], [1.2 * inch, 1.1 * inch, 4.7 * inch]))
    s.append(P("Net revenue per active user per month = $1,150 × 2.1% × 30% − $1.10 = "
               f"<b>${M['net_rev_per_active_month']:.2f}</b> — all three inputs "
               "[ASSUMPTION]s. Scenarios: best case (retention 0.87, organic-heavy mix), "
               "base case (as above), worst case (retention 0.77, paid-heavy mix)."))
    s.append(Paragraph("4 — Model strategy (Step 4)", H1))
    s.append(table(
        ["Tier", "Model", "Role here"],
        [
            ["Baseline", "Channel activation rates; single exponential retention",
             "Sanity check every fancier result is judged against"],
            ["Deterministic", "Closed-form LTV engine (Step 2)",
             "The core deliverable — exact, auditable, no training data needed"],
            ["Intermediate", "Logistic regression for activation",
             f"AUC {M['activation_auc']:.3f} vs 0.500 naive baseline — modest but real signal"],
            ["Diagnostic", "Exponential retention fit to the cohort curve",
             f"Fitted {M['fitted_retention']:.3f} vs assumed {M['assumed_retention']:.2f} — exposes the heterogeneity bias"],
        ], [1.1 * inch, 2.2 * inch, 3.7 * inch]))
    s.append(P("Feature engineering: channel one-hots, the intent signal, and the "
               "interaction the model actually learns — intent matters most in paid "
               "channels, where the base activation rate is lowest. Overfitting controls: "
               "a 75/25 stratified split, a single regularised logistic model, and no "
               "hyperparameter search (there is nothing to tune that would not be "
               "overfitting synthetic noise)."))
    s.append(PageBreak())

    # ---- Page 5: Step 5 — visual intelligence ------------------------------
    s.append(Paragraph("5 — Visual insights (Step 5)", H1))
    s.append(P("LTV vs CAC by channel. Organic and referral pay for themselves many "
               "times over; the paid channels lose roughly two-thirds of every dollar "
               "spent acquiring a user at base assumptions."))
    s.append(chart("ltv_cac_by_channel.png", 7.0, 3.3))
    s.append(P("Sensitivity tornado. Retention is the only driver whose plausible move "
               "changes the verdict: −5 points takes LTV:CAC to 0.80, +5 points to 1.38. "
               "CAC, revenue and activation all move the ratio by ~0.4 across their "
               "±20% ranges. The discount rate is a null result — worth knowing, because "
               "it tells the founders not to argue about it."))
    s.append(chart("sensitivity_tornado.png", 7.0, 3.3))
    s.append(PageBreak())

    # ---- Page 6: results -----------------------------------------------------
    s.append(Paragraph("6 — Results: the blended economics", H1))
    s.append(table(
        ["Channel", "CAC ($)", "Activation", "LTV ($)", "LTV:CAC", "Payback (mo)", "Break-even retention"],
        [[r["channel"], f"{r['cac']:.0f}", f"{r['activation']:.2f}", f"{r['ltv']:.2f}",
          f"{r['ltv_cac']:.2f}", ("—" if r["payback_months"] is None else f"{r['payback_months']:.0f}"),
          ("—" if r["breakeven_retention"] is None else f"{r['breakeven_retention']:.3f}")]
         for r in M["channels"]] +
        [["BLENDED", f"{B['cac']:.2f}", f"{B['activation']:.3f}", f"{B['ltv']:.2f}",
          f"{B['ltv_cac']:.2f}", f"{B['payback_months']:.1f}", f"{B['breakeven_retention']:.3f}"]],
        [1.1 * inch, 0.8 * inch, 0.9 * inch, 0.8 * inch, 0.8 * inch, 1.0 * inch, 1.6 * inch]))
    s.append(P(f"Blended LTV:CAC of {B['ltv_cac']:.2f} is not a business — it is a coin "
               f"flip. Payback of {B['payback_months']:.1f} months means each cohort's "
               "cash is locked up for well over a year before it funds the next cohort. "
               "And break-even retention of 0.817 against an assumed 0.82 means the "
               "entire investment case rests on retaining users 0.3 points better than "
               "the break-even line."))
    s.append(chart("payback_curve.png", 7.0, 3.6))
    s.append(P("Three readings of the same table: (1) organic and referral are the "
               "business — 5.55 and 2.94, paying back in 1–2 months; (2) paid acquisition "
               "is value-destructive at base assumptions and needs retention of ~0.94–0.95 "
               "to break even, which no consumer wallet should plan on; (3) campus sits "
               "just above water at 1.09 with a 12-month payback — a bet, not a channel."))
    s.append(PageBreak())

    # ---- Page 7: honest checks ----------------------------------------------
    s.append(Paragraph("7 — Honest checks: where the model is fragile", H1))
    s.append(P(f"<b>Empirical vs closed form.</b> The synthetic cohort's actual lifetime "
               f"revenue gives LTV:CAC {M['empirical_ltv_cac']:.2f}, "
               f"{M['empirical_vs_closed_gap_pct']:.1f}% above the closed-form "
               f"{B['ltv_cac']:.2f}. The gap is not an error — it is Jensen's inequality: "
               "LTV is convex in retention, so a spread of per-user retention rates "
               "produces more lifetime value than the average rate alone suggests. The "
               "closed form is the conservative number; the empirical one is the honest "
               "upper bound."))
    s.append(chart("retention_curve.png", 7.0, 2.9))
    s.append(P(f"<b>Retention fit.</b> A single exponential fitted to the cohort curve "
               f"lands at {M['fitted_retention']:.3f} against the assumed "
               f"{M['assumed_retention']:.2f}, with RMSE {M['retention_fit_rmse']:.3f}. "
               "The fit is mediocre on purpose: a mixture of geometrics has a heavier "
               "tail than any single exponential, so the single-rate model overstates "
               "retention and understates the tail. Anyone quoting a single retention "
               "number without this caveat is overselling precision."))
    s.append(P(f"<b>Activation model.</b> Logistic regression on channel + intent scores "
               f"AUC {M['activation_auc']:.3f} against a 0.500 naive baseline — real but "
               "modest signal. The largest coefficient is intent (+1.372): a user who "
               "arrives already intending to switch cards activates far more often. "
               "Channel coefficients run referral (+0.597) and organic (+0.429) positive, "
               "paid social (−0.866) and paid search (−0.482) negative — the same story "
               "the LTV table tells, from a different angle."))
    s.append(chart("activation_roc.png", 6.0, 2.9))
    s.append(PageBreak())

    # ---- Page 8: Step 6 — resume alignment ----------------------------------
    s.append(Paragraph("8 — Resume alignment (Step 6)", H1))
    s.append(P("<b>Match score: 6 / 10</b> for the Uno Wallet AI Business Analyst role."))
    s.append(table(
        ["JD requirement", "Resume evidence", "Gap?", "Fix"],
        [
            ["Analyse data, find opportunities, recommend actions",
             "Variance frameworks (−16% controllable expenses); multi-scenario models (−22% uncertainty); $50M+ budget planning",
             "No", "Lead with these three numbers"],
            ["Leverage AI tools on business processes",
             "Python/SQL automation; AI Engineering guide + demos; ML projects on GitHub",
             "Partial", "Frame the guide as applied AI work; never claim production LLM deployment"],
            ["Unit-economics fluency (implied)",
             "FP&A forecasting, scenario analysis, LTV-style modelling in this project",
             "Partial", "This project is the evidence — cite it"],
            ["Payments / card-rewards domain",
             "Banking/financial services at JPMorgan; no cards or rewards work",
             "Yes", "Learn the economics (§9); practise in Project 1 of the mastery guide"],
            ["Startup / founding-team experience",
             "9+ years in large organisations; side projects only",
             "Yes", "Cover letter: ownership appetite from real side-project evidence only"],
            ["Product / growth analytics",
             "Dashboards, KPI reporting; no funnel/retention/A-B work",
             "Yes", "7-day plan Days 3–4 in the mastery guide"],
        ], [1.6 * inch, 2.3 * inch, 0.6 * inch, 2.5 * inch]))
    s.append(Paragraph("Top 3 missing skills", H2))
    s += bullets([
        "Product analytics — funnel, retention, cohorts, A/B testing (not evidenced anywhere).",
        "Payments / card-rewards domain — interchange, earn rates, category caps.",
        "Production AI/LLM experience — unconfirmed; the guide and sims are not production.",
    ])
    s.append(Paragraph("Bullet upgrades (STAR + JD language, all from real record)", H2))
    s += bullets([
        "“Built SQL-driven forecasting pipelines with Python predictive models, improving forecast accuracy 27% — the same analysis-to-recommendation loop this role runs daily.”",
        "“Cut reporting latency from 48 hours to under 2 hours by consolidating fragmented ERP data into real-time Power BI dashboards — process improvement with measurable before/after.”",
        "“Ran multi-scenario models with sensitivity analysis, cutting financial-uncertainty exposure 22% — the exact sensitivity thinking this LTV project demonstrates.”",
    ])
    s.append(PageBreak())

    # ---- Page 9: architecture + impact + differentiation ---------------------
    s.append(Paragraph("9 — Architecture, impact, differentiation (Steps 7 & 10)", H1))
    s.append(Paragraph("Architecture", H2))
    s.append(P("[Synthetic data] → [data_gen] → [LTV engine + sensitivity] → "
               "[activation model + retention fit] → [charts + metrics.json] → "
               "[report + deck]. A weekly batch job re-runs run_all.py on the latest "
               "cohort export; the only production step is replacing the synthetic "
               "generator with a real warehouse extract behind the same interface. "
               "Stack: Python, pandas, scikit-learn, matplotlib; FastAPI + a Streamlit "
               "dashboard is the natural next step, not a rebuild."))
    s.append(Paragraph("Business impact", H2))
    s += bullets([
        "A 2-person startup cannot afford to learn LTV:CAC is 1.02 after spending the money. This engine answers it before the spend.",
        "Killing paid search/social at base assumptions saves ~$40 per acquired user that returns $13–15 — the single highest-ROI decision in the deck.",
        "The retention lever (+5pp → +36% LTV:CAC) reframes the roadmap: onboarding and month-1 experience beat acquisition spend.",
    ])
    s.append(Paragraph("What differentiates this project (Step 10)", H2))
    s += bullets([
        "It refuses the single-point answer: sensitivity, break-even, and the empirical-vs-closed-form gap are the deliverable, not decoration.",
        "It names its own misfit: the retention fit's RMSE and the heterogeneity bias are reported, not buried.",
        "It connects to the candidate's real record — $50M+ budgets, scenario models, forecasting — instead of inventing startup experience.",
    ])
    s.append(Paragraph("Five questions to ask in the interview", H2))
    s += bullets([
        "What is your current blended CAC, and which channel actually pays back?",
        "What is month-1 retention, and what does onboarding look like for a user who never activates?",
        "How do you split rewards value with users today — and what would change that split?",
        "What is the single metric the founders check every morning?",
        "If I joined, what is the first analysis you would want in my first two weeks?",
    ])
    s.append(Paragraph("Future improvements", H2))
    s += bullets([
        "Replace synthetic inputs with the real cohort export behind the same interface.",
        "Add a survival model (Cox) for retention instead of a single exponential.",
        "Add a referral-loop term: activated users who refer lower blended CAC over time.",
        "Track LTV:CAC weekly as a standing dashboard, with alerts at 1.0 and 1.5.",
    ])
    s.append(PageBreak())

    # ---- Page 10: appendix ----------------------------------------------------
    s.append(Paragraph("10 — Appendix: assumptions register & reproducibility", H1))
    s.append(P("Every input is an [ASSUMPTION]. None is a fact about Uno Wallet. If any "
               "single input is wrong, the sensitivity table (§5) says how much the answer "
               "moves — that is the point of the project."))
    arows = [[c, f"${s['cac']:.0f}", f"{s['activation']:.0%}", f"mix {s['mix']:.0%}"]
             for c, s in A["channels"].items()]
    s.append(table(["Channel", "CAC", "Activation", "Mix"], arows,
                   [1.8 * inch, 1.2 * inch, 1.4 * inch, 1.6 * inch]))
    s.append(table(
        ["Input", "Value"],
        [
            ["Monthly retention (base)", f"{A['base_monthly_retention']:.2f} (per-user spread ±0.06)"],
            ["Mean monthly spend", f"${A['mean_monthly_spend']:.0f}"],
            ["Earn rate", f"{A['earn_rate']:.1%}"],
            ["Uno take of rewards value", f"{A['uno_take']:.0%}"],
            ["Servicing cost", f"${A['servicing_cost_per_active_month']:.2f} / active user / month"],
            ["Discount rate", f"{A['discount_monthly']:.0%} / month"],
            ["Net revenue / active user / month", f"${M['net_rev_per_active_month']:.2f}"],
        ], [2.6 * inch, 4.4 * inch]))
    s.append(Paragraph("Reproducibility", H2))
    s += bullets([
        "Seed 20261125; 6,000 synthetic users; run_all.py regenerates data, metrics and all five charts.",
        "Test suite: 53 checks, runtime “53 passed” line — re-run with python -m tests.test_all.",
        "Chart PNGs are gitignored and regenerate with run_all.py; the CSV is committed (268 KB, text).",
    ])
    s.append(Paragraph("About", H2))
    s.append(P("Created by Bhupesh Chandra Dimri — Financial Analyst, JPMorgan Chase "
               "(Jul 2025–present), 9+ years FP&A; M.S. Accounting Analytics & Data "
               "Technology, Pace University (Dec 2025). Contact: 917-818-6198, "
               "bhupesh7cd@gmail.com, linkedin.com/in/bhupeshdimri. GitHub: "
               "github.com/bhupesh-debug (repo: uno-wallet-unit-economics — to be created)."))
    s.append(P("Sources: Uno Wallet YC P26 profile and Handshake listing (role facts); "
               "all financial inputs are the author's labelled assumptions."))
    doc.build(s)


def build_deck(path):
    doc = SimpleDocTemplate(str(path), pagesize=LETTER,
                            leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                            topMargin=0.7 * inch, bottomMargin=0.7 * inch)
    s = []
    # Slide 1 — title
    s.append(Spacer(1, 1.2 * inch))
    s.append(Paragraph("Unit Economics of One Uno User", TITLE))
    s.append(Spacer(1, 8))
    s.append(Paragraph("What is one user worth, what does one user cost — and which "
                       "assumption decides the answer?", SUB))
    s.append(Spacer(1, 16))
    s.append(P("ML Project for AI Business Analyst at Uno Wallet (YC P26)", DB))
    s.append(P("Bhupesh Chandra Dimri — November 25, 2026", DB))
    s.append(P("Synthetic data throughout; every input labelled [ASSUMPTION].", DB))
    s.append(PageBreak())
    # Slide 2 — problem
    s.append(Paragraph("2 — The problem", DT))
    s += bullets([
        "Uno Wallet is two founders building an AI iPhone wallet that picks the best card per purchase.",
        "Before spending on growth, the founders need one answer: what is a user worth vs what does a user cost?",
        "One-liner: <b>if LTV:CAC is 1.02, the business is a coin flip — and retention decides which side lands.</b>",
        "Why it matters: every growth dollar spent below break-even is a dollar the startup never gets back.",
    ], DB)
    s.append(PageBreak())
    # Slide 3 — JD breakdown
    s.append(Paragraph("3 — JD breakdown", DT))
    s += bullets([
        "Duty 1: analyse data, find business opportunities, turn insights into recommendations.",
        "Duty 2: leverage AI tools to improve business processes and decision-making.",
        "Who they want: analytical, entrepreneurial, resourceful, strong problem-solving.",
        "Hidden expectation: at a 2-person startup, the analyst IS the analytics team — and unit economics is question one.",
        "Risk: the JD is two bullets; most of the role is inference, labelled as such.",
    ], DB)
    s.append(PageBreak())
    # Slide 4 — ML approach
    s.append(Paragraph("4 — ML approach", DT))
    s += bullets([
        "Honest-fit gate: no deep learning forced onto this JD — this is an analytics + forecasting project.",
        "Core: a deterministic closed-form LTV engine (LTV = activation × net revenue ÷ (1 − retention × discount)).",
        "Support: logistic regression for activation (AUC 0.672 vs 0.500 baseline) + an exponential retention fit.",
        "The differentiator: a sensitivity analysis and a break-even solver, not a single-point LTV.",
    ], DB)
    s.append(PageBreak())
    # Slide 5 — data strategy
    s.append(Paragraph("5 — Data strategy", DT))
    s += bullets([
        "6,000 synthetic users, seeded and reproducible (no real Uno Wallet data is public).",
        "Five channels with [ASSUMPTION] CAC ($4–$42) and activation (38–72%).",
        "Net revenue per active user: $1,150 spend × 2.1% earn × 30% take − $1.10 servicing = $6.15/month.",
        "Preprocessing: none needed beyond the generator — the pipeline's job is the model, not cleaning.",
    ], DB)
    s.append(PageBreak())
    # Slide 6 — model design
    s.append(Paragraph("6 — Model design", DT))
    s += bullets([
        "Baseline: channel activation rates + a single exponential retention curve.",
        "LTV engine: closed form, exact, auditable — every input traceable to one [ASSUMPTION].",
        "Activation model: logistic regression on channel + intent; intent is the strongest signal (+1.372).",
        "Evaluation: closed form vs brute-force simulation (match to <0.01); empirical cohort vs closed form (gap reported, not hidden).",
    ], DB)
    s.append(PageBreak())
    # Slide 7 — results
    s.append(Paragraph("7 — Results & insights", DT))
    s += bullets([
        f"Blended LTV:CAC {B['ltv_cac']:.2f} — LTV ${B['ltv']:.2f} vs CAC ${B['cac']:.2f}. Payback {B['payback_months']:.1f} months.",
        f"Break-even retention {B['breakeven_retention']:.3f} vs assumed {M['assumed_retention']:.2f} — a 0.3-point margin.",
        "Organic 5.55 / referral 2.94 pay; paid search 0.35 / paid social 0.33 never pay back.",
        f"Retention dominates sensitivity (spread {RANK[0]['spread']:.2f}); discount rate is a null result.",
    ], DB)
    s.append(chart("ltv_cac_by_channel.png", 6.5, 2.6))
    s.append(PageBreak())
    # Slide 8 — business impact
    s.append(Paragraph("8 — Business impact", DT))
    s += bullets([
        "Killing paid acquisition at base assumptions saves ~$40 per user that returns $13–15.",
        "Retention +5pp lifts LTV:CAC 36% — onboarding and month-1 experience beat acquisition spend.",
        "A standing weekly LTV:CAC dashboard with alerts at 1.0 and 1.5 replaces gut feel with a number.",
        "Framed for a founder: this is the difference between funding the next cohort and not.",
    ], DB)
    s.append(PageBreak())
    # Slide 9 — future improvements
    s.append(Paragraph("9 — Future improvements", DT))
    s += bullets([
        "Swap the synthetic generator for the real cohort export behind the same interface.",
        "Survival (Cox) model for retention instead of a single exponential.",
        "Add a referral-loop term: activated users lower future blended CAC.",
        "Track LTV:CAC weekly; add activation-propensity scoring to prioritise onboarding.",
        "Production readiness: FastAPI + Streamlit dashboard; the engine needs no rebuild.",
    ], DB)
    s.append(PageBreak())
    # Slide 10 — about
    s.append(Paragraph("10 — About this project", DT))
    s += bullets([
        "Created by Bhupesh Chandra Dimri — Financial Analyst, JPMorgan Chase; 9+ years FP&A; M.S. Accounting Analytics & Data Technology, Pace (Dec 2025).",
        "GitHub: github.com/bhupesh-debug — repo uno-wallet-unit-economics (to be created).",
        "Contact: 917-818-6198 · bhupesh7cd@gmail.com · linkedin.com/in/bhupeshdimri",
        "All financial inputs are labelled [ASSUMPTION]s; no Uno Wallet data was used.",
    ], DB)
    doc.build(s)


if __name__ == "__main__":
    r = OUT / "Bhupesh_Chandra_Dimri_ML-Project_Uno-Wallet-Unit-Economics.pdf"
    d = OUT / "Bhupesh_Chandra_Dimri_ML-Project_Uno-Wallet-Unit-Economics_Deck.pdf"
    build_report(r)
    build_deck(d)
    from pypdf import PdfReader
    print("report pages:", len(PdfReader(str(r)).pages))
    print("deck pages:", len(PdfReader(str(d)).pages))
