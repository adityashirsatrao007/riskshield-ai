import logging
import threading
from collections import deque
from datetime import datetime, timezone
from typing import Any

from prometheus_client import Counter, Gauge, Histogram, Summary

logger = logging.getLogger("riskshield")

PREDICTIONS_TOTAL = Counter(
    "riskshield_predictions_total",
    "Total number of predictions made",
    ["merchant_id", "risk_level"],
)

FRAUD_DETECTED_TOTAL = Counter(
    "riskshield_fraud_detected_total",
    "Total number of flagged fraudulent transactions",
    ["merchant_id"],
)

RISK_SCORE_HISTOGRAM = Histogram(
    "riskshield_risk_score",
    "Distribution of risk scores",
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
)

PROCESSING_TIME = Summary(
    "riskshield_processing_time_ms",
    "Model inference time in milliseconds",
)

PREDICTION_BATCH_SIZE = Gauge(
    "riskshield_prediction_batch_size",
    "Size of the last batch prediction",
)

DRIFT_DETECTED = Counter(
    "riskshield_drift_detected_total",
    "Total number of drift detection alerts",
)

ACTIVE_MERCHANTS = Gauge(
    "riskshield_active_merchants",
    "Number of active merchants",
)


class PredictionLogger:
    def __init__(self, max_history: int = 10000):
        self._history: deque[dict[str, Any]] = deque(maxlen=max_history)
        self._lock = threading.Lock()
        self._total_count = 0
        self._flagged_count = 0

    def log(
        self,
        transaction_id: str,
        merchant_id: str,
        risk_score: float,
        risk_level: str,
        is_flagged: bool,
        processing_time_ms: float,
        features_used: list[str],
        timestamp: datetime | None = None,
    ) -> None:
        entry = {
            "transaction_id": transaction_id,
            "merchant_id": merchant_id,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "is_flagged": is_flagged,
            "processing_time_ms": processing_time_ms,
            "features_used": features_used,
            "timestamp": (timestamp or datetime.now(timezone.utc)).isoformat(),
        }
        with self._lock:
            self._history.append(entry)
            self._total_count += 1
            if is_flagged:
                self._flagged_count += 1

        PREDICTIONS_TOTAL.labels(merchant_id=merchant_id, risk_level=risk_level).inc()
        RISK_SCORE_HISTOGRAM.observe(risk_score)
        PROCESSING_TIME.observe(processing_time_ms)
        if is_flagged:
            FRAUD_DETECTED_TOTAL.labels(merchant_id=merchant_id).inc()

    def get_recent(self, n: int = 100) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._history)[-n:]

    def get_stats(self) -> dict[str, Any]:
        with self._lock:
            total = self._total_count
            flagged = self._flagged_count
            recent = list(self._history)[-1000:]

        scores = [e["risk_score"] for e in recent]
        avg_score = sum(scores) / len(scores) if scores else 0.0

        return {
            "total_predictions": total,
            "flagged_predictions": flagged,
            "fraud_rate": round((flagged / total * 100), 2) if total > 0 else 0.0,
            "avg_risk_score": round(avg_score, 4),
            "recent_count": len(recent),
        }

    def get_score_distribution(self, n: int = 1000) -> dict[str, int]:
        with self._lock:
            recent = list(self._history)[-n:]

        dist = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for entry in recent:
            level = entry.get("risk_level", "low")
            if level in dist:
                dist[level] += 1
        return dist


def _compute_psi(expected: list[float], actual: list[float], bins: int = 10) -> float:
    if not expected or not actual:
        return 0.0

    min_val = min(min(expected), min(actual))
    max_val = max(max(expected), max(actual))
    if min_val == max_val:
        return 0.0

    bin_edges = [min_val + i * (max_val - min_val) / bins for i in range(bins + 1)]

    def _histogram(data: list[float]) -> list[float]:
        counts = [0.0] * bins
        for v in data:
            for j in range(bins):
                if bin_edges[j] <= v < bin_edges[j + 1]:
                    counts[j] += 1
                    break
            else:
                counts[-1] += 1
        total = len(data)
        return [c / total if total > 0 else 0.0001 for c in counts]

    expected_pcts = _histogram(expected)
    actual_pcts = _histogram(actual)

    psi = 0.0
    for e, a in zip(expected_pcts, actual_pcts):
        e = max(e, 0.0001)
        a = max(a, 0.0001)
        psi += (a - e) * (a / e - 1)
    return psi


class DriftDetector:
    def __init__(self, psi_threshold: float = 0.2, baseline_window: int = 5000):
        self._psi_threshold = psi_threshold
        self._baseline_window = baseline_window
        self._baseline_scores: list[float] = []
        self._lock = threading.Lock()

    def set_baseline(self, scores: list[float]) -> None:
        with self._lock:
            self._baseline_scores = scores[-self._baseline_window:]

    def check_drift(self, recent_scores: list[float]) -> dict[str, Any]:
        with self._lock:
            baseline = list(self._baseline_scores)

        if len(baseline) < 100 or len(recent_scores) < 50:
            return {"drift_detected": False, "psi": 0.0, "reason": "insufficient_data"}

        psi = _compute_psi(baseline, recent_scores)
        drift = psi > self._psi_threshold

        if drift:
            DRIFT_DETECTED.inc()
            logger.warning("Model drift detected: PSI=%.4f (threshold=%.4f)", psi, self._psi_threshold)

        return {
            "drift_detected": drift,
            "psi": round(psi, 4),
            "threshold": self._psi_threshold,
            "baseline_size": len(baseline),
            "recent_size": len(recent_scores),
        }


class MetricsCollector:
    _predictions_counter = PREDICTIONS_TOTAL
    _flagged_counter = FRAUD_DETECTED_TOTAL
    _prediction_latency = PROCESSING_TIME

    def __init__(self, prediction_logger: PredictionLogger, drift_detector: DriftDetector):
        self.prediction_logger = prediction_logger
        self.drift_detector = drift_detector

    def get_prometheus_metrics(self) -> dict[str, Any]:
        stats = self.prediction_logger.get_stats()
        dist = self.prediction_logger.get_score_distribution()
        recent = self.prediction_logger.get_recent(500)
        recent_scores = [e["risk_score"] for e in recent]
        drift = self.drift_detector.check_drift(recent_scores)

        return {
            "stats": stats,
            "distribution": dist,
            "drift": drift,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_model_info(self) -> dict[str, Any]:
        from app.services import risk_engine

        return {
            "model_loaded": risk_engine.is_loaded(),
            "model_version": risk_engine.get_model_version(),
            "features": risk_engine.get_feature_names(),
            "threshold": risk_engine.get_threshold(),
            "model_type": "random_forest",
        }


class AlertManager:
    def __init__(self, drift_detector: DriftDetector, fraud_rate_threshold: float = 5.0):
        self._drift_detector = drift_detector
        self._fraud_rate_threshold = fraud_rate_threshold
        self._alerts: deque[dict[str, Any]] = deque(maxlen=500)
        self._lock = threading.Lock()

    def check_fraud_rate(self, stats: dict[str, Any]) -> dict[str, Any] | None:
        rate = stats.get("fraud_rate", 0.0)
        if rate > self._fraud_rate_threshold:
            alert = {
                "type": "fraud_rate_spike",
                "severity": "high" if rate > self._fraud_rate_threshold * 2 else "medium",
                "fraud_rate": rate,
                "threshold": self._fraud_rate_threshold,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message": f"Fraud rate {rate:.1f}% exceeds threshold {self._fraud_rate_threshold}%",
            }
            with self._lock:
                self._alerts.append(alert)
            logger.warning("Fraud rate spike alert: %.1f%%", rate)
            return alert
        return None

    def check_drift_alert(self, recent_scores: list[float]) -> dict[str, Any] | None:
        result = self._drift_detector.check_drift(recent_scores)
        if result["drift_detected"]:
            alert = {
                "type": "model_drift",
                "severity": "high",
                "psi": result["psi"],
                "threshold": result["threshold"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message": f"Model drift detected: PSI={result['psi']:.4f}",
            }
            with self._lock:
                self._alerts.append(alert)
            return alert
        return None

    def get_recent_alerts(self, n: int = 50) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._alerts)[-n:]
