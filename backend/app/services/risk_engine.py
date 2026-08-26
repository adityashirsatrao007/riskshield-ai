import os
import time
import logging
import threading

import numpy as np

logger = logging.getLogger("riskshield")

_lock = threading.Lock()
_model = None
_scaler = None
_metadata = None
_threshold = 0.5
_feature_names: list[str] = []
_model_version = "unknown"
_model_type = "unknown"

_FEATURE_NAMES = [
    "V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9", "V10",
    "V11", "V12", "V13", "V14", "V15", "V16", "V17", "V18", "V19", "V20",
    "V21", "V22", "V23", "V24", "V25", "V26", "V27", "V28",
    "Time", "Amount", "amount_log", "amount_zscore", "hour_of_day", "is_high_amount",
]

_CARD_TYPE_MAP = {"credit": 0, "debit": 1, "upi": 2, "netbanking": 3, "wallet": 4, "prepaid": 5}


def load_model(model_path: str) -> None:
    global _model, _scaler, _metadata, _threshold, _feature_names, _model_version, _model_type

    with _lock:
        import joblib
        bundle = joblib.load(model_path)
        _model = bundle["model"]
        _scaler = bundle.get("scaler")
        _metadata = bundle.get("metadata", {})
        _threshold = bundle.get("threshold", 0.5)
        _feature_names = bundle.get("features", list(_FEATURE_NAMES))
        _model_version = _metadata.get("version", "1.0.0")
        _model_type = type(_model).__name__
        logger.info(
            "Model loaded: %s (v%s, threshold=%.3f)",
            _model_type, _model_version, _threshold,
        )


def is_loaded() -> bool:
    with _lock:
        return _model is not None


def get_model_version() -> str:
    with _lock:
        return _model_version


def get_feature_names() -> list[str]:
    with _lock:
        return list(_feature_names)


def get_threshold() -> float:
    with _lock:
        return _threshold


def _approximate_v_features(amount: float, amount_log: float, amount_zscore: float, hour: int) -> np.ndarray:
    rng = np.random.RandomState(abs(hash((amount, hour))) % (2**31))
    base = rng.randn(28) * 0.5
    base[0] = amount_zscore * 0.3
    base[1] = amount_log * 0.1
    base[2] = np.sin(hour / 24 * 2 * np.pi) * 0.4
    base[3] = np.cos(hour / 24 * 2 * np.pi) * 0.3
    base[4] = (amount / 10000) * 0.2
    base[6] = rng.uniform(-1, 1) * 0.3
    base[9] = rng.uniform(-1, 1) * 0.25
    base[14] = np.log1p(amount) * 0.15
    base[17] = rng.uniform(-0.5, 0.5)
    base = np.clip(base, -5, 5)
    return base


def _extract_features(txn: dict) -> tuple[np.ndarray, list[str]]:
    amount = float(txn.get("amount", 0))
    amount_log = float(np.log1p(amount))

    meta = _metadata or {}
    amount_mean = meta.get("amount_mean", 1000.0)
    amount_std = meta.get("amount_std", 5000.0)
    amount_zscore = (amount - amount_mean) / (amount_std + 1e-8)

    ts_str = txn.get("timestamp")
    if ts_str:
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(ts_str)
            hour = dt.hour
            time_seconds = dt.hour * 3600 + dt.minute * 60 + dt.second
        except (ValueError, TypeError):
            hour = txn.get("hour_of_day", 12)
            time_seconds = hour * 3600
    else:
        hour = txn.get("hour_of_day", 12)
        time_seconds = txn.get("time", hour * 3600)

    high_amount_threshold = meta.get("high_amount_threshold", 5000)
    is_high_amount = 1 if amount > high_amount_threshold else 0

    v_features = _approximate_v_features(amount, amount_log, amount_zscore, hour)

    feature_values = v_features.tolist()
    feature_values.append(float(time_seconds))
    feature_values.append(amount)
    feature_values.append(amount_log)
    feature_values.append(amount_zscore)
    feature_values.append(float(hour))
    feature_values.append(float(is_high_amount))

    return np.array([feature_values]), _FEATURE_NAMES[:len(feature_values)]


def score_transaction(transaction_data: dict) -> dict:
    start = time.time()

    if not is_loaded():
        logger.warning("Model not loaded, returning fallback score")
        return {
            "risk_score": 0.0,
            "risk_level": "unknown",
            "is_flagged": False,
            "explanations": [{"feature": "model_status", "value": 0, "importance": 0, "description": "Model not loaded"}],
            "model_version": "unknown",
            "processing_time_ms": round((time.time() - start) * 1000, 2),
            "features_used": [],
        }

    with _lock:
        X, feature_names_used = _extract_features(transaction_data)
        X_scaled = _scaler.transform(X) if _scaler else X
        proba = _model.predict_proba(X_scaled)[0]
        risk_score = float(proba[1])

        threshold = _threshold

    if risk_score >= 0.8:
        risk_level = "critical"
    elif risk_score >= 0.6:
        risk_level = "high"
    elif risk_score >= 0.3:
        risk_level = "medium"
    else:
        risk_level = "low"

    importances = {}
    if hasattr(_model, "feature_importances_") and len(_model.feature_importances_) == X.shape[1]:
        importances = dict(zip(feature_names_used, _model.feature_importances_))

    feature_values = dict(zip(feature_names_used, X[0].tolist()))

    explanations = []
    sorted_features = sorted(importances.keys(), key=lambda k: -abs(importances[k]))[:5]
    for feat in sorted_features:
        val = feature_values[feat]
        imp = importances[feat]
        explanations.append({
            "feature": feat,
            "value": round(float(val), 4),
            "importance": round(float(imp), 4),
            "description": f"{feat} = {round(float(val), 2)}",
        })

    if not explanations:
        top_idx = np.argsort(-np.abs(X[0]))[:5]
        for idx in top_idx:
            fname = feature_names_used[idx]
            explanations.append({
                "feature": fname,
                "value": round(float(X[0][idx]), 4),
                "importance": 0.0,
                "description": f"{fname} = {round(float(X[0][idx]), 2)}",
            })

    processing_time_ms = round((time.time() - start) * 1000, 2)

    return {
        "risk_score": round(risk_score, 4),
        "risk_level": risk_level,
        "is_flagged": risk_score >= threshold,
        "explanations": explanations,
        "model_version": _model_version,
        "processing_time_ms": processing_time_ms,
        "features_used": feature_names_used,
    }
