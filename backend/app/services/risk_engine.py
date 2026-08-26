import time
import logging
import numpy as np

logger = logging.getLogger("riskshield")

_model = None
_scaler = None
_metadata = None
_threshold = None
_features = None


def load_model(model_path: str):
    global _model, _scaler, _metadata, _threshold, _features
    import joblib
    bundle = joblib.load(model_path)
    _model = bundle["model"]
    _scaler = bundle["scaler"]
    _metadata = bundle["metadata"]
    _threshold = bundle["threshold"]
    _features = bundle["features"]
    logger.info("Model loaded: %s", bundle["model"].__class__.__name__)


def _check_model():
    if _model is None:
        raise RuntimeError("Model not loaded. Call load_model() first.")


def _extract_features(txn: dict) -> np.ndarray:
    _check_model()
    amount = float(txn.get("amount", 0))
    amount_mean = _metadata["amount_mean"]
    amount_std = _metadata["amount_std"]

    amount_zscore = (amount - amount_mean) / (amount_std + 1e-8)
    amount_log = np.log1p(amount)
    merchant_avg = float(txn.get("merchant_avg_ticket_size", 1))
    txn_to_avg = amount / (merchant_avg + 1)
    account_age = int(txn.get("customer_account_age_days", 0))
    total_txn = int(txn.get("customer_total_transactions", 0))
    hour = int(txn.get("hour_of_day", 12))
    day = int(txn.get("day_of_week", 0))

    if account_age <= 7:
        account_age_bucket = 0
    elif account_age <= 30:
        account_age_bucket = 1
    elif account_age <= 90:
        account_age_bucket = 2
    elif account_age <= 365:
        account_age_bucket = 3
    else:
        account_age_bucket = 4

    txn_frequency = total_txn / (account_age + 1)
    is_night = 1 if (hour >= 22 or hour <= 5) else 0
    is_weekend = 1 if day >= 5 else 0

    is_international = int(txn.get("is_international", 0))
    shipping_match = int(txn.get("shipping_address_match", 1))
    device_reused = int(txn.get("device_fingerprint_reused", 0))

    risk_flags = (
        is_international + (1 - shipping_match) + device_reused +
        is_night + (1 if amount_zscore > 2 else 0) + (1 if account_age < 30 else 0)
    )

    encoders = _metadata["label_encoders"]
    try:
        card_type = encoders["card_type"].transform([txn.get("card_type", "credit")])[0]
    except Exception:
        card_type = 0
    try:
        card_network = encoders["card_network"].transform([txn.get("card_network", "visa")])[0]
    except Exception:
        card_network = 0
    try:
        merchant_cat = encoders["merchant_category"].transform([txn.get("merchant_category_code", "electronics")])[0]
    except Exception:
        merchant_cat = 0
    try:
        country = encoders["country"].transform([txn.get("country_code", "IN")])[0]
    except Exception:
        country = 0

    return np.array([[
        amount, amount_log, amount_zscore, hour, day,
        is_international, account_age, total_txn,
        merchant_avg, shipping_match, device_reused,
        txn_to_avg, account_age_bucket, txn_frequency,
        is_night, is_weekend, risk_flags,
        card_type, card_network, merchant_cat, country
    ]])


def score_transaction(txn: dict) -> dict:
    _check_model()
    start = time.time()

    X = _extract_features(txn)
    X_scaled = _scaler.transform(X)
    proba = _model.predict_proba(X_scaled)[0]
    risk_score = float(proba[1])

    if risk_score >= 0.8:
        risk_level = "critical"
    elif risk_score >= 0.6:
        risk_level = "high"
    elif risk_score >= 0.3:
        risk_level = "medium"
    else:
        risk_level = "low"

    importances = dict(zip(_features, _model.feature_importances_))
    feature_values = dict(zip(_features, X[0].tolist()))

    explanations = []
    for feat in sorted(importances, key=lambda k: -abs(importances[k]))[:3]:
        val = feature_values[feat]
        imp = importances[feat]
        explanations.append({
            "feature": feat,
            "value": round(float(val), 4),
            "importance": round(float(imp), 4),
            "description": f"{feat} = {round(float(val), 2)}"
        })

    processing_time_ms = (time.time() - start) * 1000

    return {
        "risk_score": round(risk_score, 4),
        "risk_level": risk_level,
        "is_flagged": risk_score >= _threshold,
        "explanations": explanations,
        "model_version": "1.0.0",
        "processing_time_ms": round(processing_time_ms, 2),
    }
