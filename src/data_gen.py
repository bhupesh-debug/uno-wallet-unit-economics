"""Synthetic user-level data for the Uno Wallet unit-economics project.

EVERY number below is an [ASSUMPTION] — a labelled modelling input, NOT a fact
about Uno Wallet. Uno Wallet has published no acquisition costs, activation rates,
retention, spend, or revenue figures; this dataset is a synthetic stand-in built
so the LTV/CAC machinery can be demonstrated and stress-tested honestly.
"""
import numpy as np
import pandas as pd

SEED = 20261125
N_USERS = 6000

# --- [ASSUMPTION] channel mix, CAC, activation rate per channel -------------
CHANNELS = {
    "organic":      {"mix": 0.30, "cac": 4.0,  "activation": 0.68},
    "referral":     {"mix": 0.25, "cac": 8.0,  "activation": 0.72},
    "paid_social":  {"mix": 0.20, "cac": 38.0, "activation": 0.38},
    "paid_search":  {"mix": 0.15, "cac": 42.0, "activation": 0.45},
    "campus":       {"mix": 0.10, "cac": 18.0, "activation": 0.60},
}

# --- [ASSUMPTION] retention, spend, revenue economics -----------------------
BASE_MONTHLY_RETENTION = 0.82   # per activated user, per month
RETENTION_SPREAD = 0.06         # user-level heterogeneity (std of beta draw)
MEAN_MONTHLY_SPEND = 1150.0     # $ per active user per month
SPEND_SIGMA = 0.55              # lognormal spread of monthly spend
EARN_RATE = 0.021               # rewards earned as a share of spend (2.1%)
UNO_TAKE = 0.30                 # share of rewards value Uno keeps [ASSUMPTION]
SERVICING_COST = 1.10           # $ per active user per month [ASSUMPTION]
DISCOUNT_MONTHLY = 0.01         # 1% per month discount rate [ASSUMPTION]
HORIZON_MONTHS = 36

# Derived economics (per active user per month, before retention/discount)
NET_REV_PER_ACTIVE_MONTH = MEAN_MONTHLY_SPEND * EARN_RATE * UNO_TAKE - SERVICING_COST


def generate_users(n=N_USERS, seed=SEED):
    """Generate one row per acquired user with a synthetic activation, retention
    and spend profile. Returns a DataFrame."""
    rng = np.random.default_rng(seed)
    names = list(CHANNELS)
    mix = np.array([CHANNELS[c]["mix"] for c in names])
    channel = rng.choice(names, size=n, p=mix)

    activation_p = np.array([CHANNELS[c]["activation"] for c in channel])
    # A pre-signup intent signal (0-1) shifts activation odds; used as a model feature.
    intent = rng.beta(2.0, 2.0, size=n)
    adj_p = np.clip(activation_p + 0.25 * (intent - 0.5), 0.05, 0.95)
    activated = rng.random(n) < adj_p

    # Per-user monthly retention, heterogeneous around the base rate.
    retention = np.clip(
        rng.normal(BASE_MONTHLY_RETENTION, RETENTION_SPREAD, size=n), 0.55, 0.97
    )
    # Months active for activated users: geometric with p = 1 - retention.
    months_active = np.zeros(n, dtype=int)
    act_idx = np.where(activated)[0]
    months_active[act_idx] = rng.geometric(1.0 - retention[act_idx])
    months_active = np.clip(months_active, 0, HORIZON_MONTHS)

    # Monthly spend for activated users (lognormal, capped at horizon).
    spend = np.zeros(n)
    spend[act_idx] = rng.lognormal(
        mean=np.log(MEAN_MONTHLY_SPEND) - 0.5 * SPEND_SIGMA ** 2,
        sigma=SPEND_SIGMA, size=len(act_idx),
    )
    # Lifetime revenue per user: discounted sum of monthly net revenue while
    # active. NOTE: in a realised path, an active month pays the FULL monthly
    # net revenue — the retention factor r^t belongs in the EXPECTED-value
    # formula only (it is the probability of still being active at t).
    # Multiplying realised revenue by r^t as well would double-discount it.
    lifetime_rev = np.zeros(n)
    for i in act_idx:
        m = months_active[i]
        t = np.arange(m)
        monthly_net = spend[i] * EARN_RATE * UNO_TAKE - SERVICING_COST
        lifetime_rev[i] = float(np.sum(monthly_net * (1 - DISCOUNT_MONTHLY) ** t))

    cac = np.array([CHANNELS[c]["cac"] for c in channel])
    df = pd.DataFrame({
        "user_id": np.arange(n),
        "channel": channel,
        "intent": np.round(intent, 3),
        "cac": cac,
        "activated": activated.astype(int),
        "retention": np.round(retention, 3),
        "months_active": months_active,
        "monthly_spend": np.round(spend, 2),
        "lifetime_rev": np.round(lifetime_rev, 2),
    })
    return df


if __name__ == "__main__":
    df = generate_users()
    df.to_csv("data/synthetic/users.csv", index=False)
    print(f"wrote {len(df)} users")
    print(df.groupby("channel")[["cac", "activated", "months_active", "lifetime_rev"]].mean().round(2))
