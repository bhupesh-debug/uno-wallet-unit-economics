"""Predictive models on the synthetic user data.

1. Activation classifier — logistic regression on (channel one-hots + intent)
   vs a naive baseline that predicts the overall activation rate for everyone.
   Honest comparison: if the model cannot beat the rate baseline, say so.
2. Retention-curve fit — an exponential decay fitted to the empirical cohort
   retention curve, compared with the raw empirical curve. The gap between the
   empirical LTV (from the observed curve) and the closed-form exponential LTV
   is reported honestly in evaluate.py.
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder


def activation_model(df, seed=20261125):
    """Fit logistic regression to predict activation. Returns metrics + model."""
    X = pd.get_dummies(df[["channel", "intent"]], columns=["channel"], drop_first=False)
    y = df["activated"].values
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=seed, stratify=y)
    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train)
    proba = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, proba)
    # Naive baseline: predict the train activation rate for everyone.
    base_rate = float(y_train.mean())
    base_auc = 0.5  # a constant prediction has no ranking power
    coefs = {c: round(float(v), 3) for c, v in zip(X.columns, model.coef_[0])}
    return {
        "model": model,
        "auc": round(float(auc), 3),
        "baseline_auc": base_auc,
        "baseline_rate": round(base_rate, 3),
        "n_train": int(len(y_train)),
        "n_test": int(len(y_test)),
        "coefficients": coefs,
        "feature_names": list(X.columns),
        "X_test": X_test,
        "y_test": y_test,
        "proba_test": proba,
    }


def empirical_retention_curve(df, horizon=36):
    """Share of activated users still active at each month, from the synthetic
    months_active column (a step-function cohort curve)."""
    act = df[df["activated"] == 1]
    curve = []
    for t in range(horizon + 1):
        curve.append(float((act["months_active"] > t).mean()))
    return np.array(curve)


def fit_exponential_retention(curve, horizon=36):
    """Fit retention(t) = r^t by least squares on log(retention). Returns r and
    the fitted curve."""
    t = np.arange(1, horizon + 1)
    y = curve[1:]
    mask = y > 0.01
    log_r = float(np.polyfit(t[mask], np.log(y[mask]), 1)[0])
    r = float(np.exp(log_r))
    fitted = np.array([r ** k for k in range(horizon + 1)])
    return {"retention": round(r, 3), "fitted": fitted,
            "rmse": round(float(np.sqrt(np.mean((curve - fitted) ** 2))), 4)}
