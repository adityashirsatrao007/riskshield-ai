import os
import json
import datetime
import numpy as np
import pandas as pd
from pathlib import Path

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MONITOR_DIR = os.path.join(SCRIPT_DIR, "..", "monitoring")
METRICS_FILE = os.path.join(MONITOR_DIR, "monitor_metrics.json")
PREDICTIONS_LOG = os.path.join(MONITOR_DIR, "predictions_log.jsonl")
REFERENCE_DATA_PATH = os.path.join(SCRIPT_DIR, "..", "data", "creditcard.csv")


def ensure_dirs() -> None:
    os.makedirs(MONITOR_DIR, exist_ok=True)


def compute_psi(expected: np.ndarray, actual: np.ndarray, n_bins: int = 10) -> float:
    eps = 1e-6
    min_val = min(expected.min(), actual.min())
    max_val = max(expected.max(), actual.max())
    bins = np.linspace(min_val - eps, max_val + eps, n_bins + 1)

    expected_counts = np.histogram(expected, bins=bins)[0].astype(float)
    actual_counts = np.histogram(actual, bins=bins)[0].astype(float)

    expected_pct = expected_counts / expected_counts.sum() + eps
    actual_pct = actual_counts / actual_counts.sum() + eps

    psi = float(np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct)))
    return psi


def compute_distribution_stats(values: np.ndarray) -> dict:
    return {
        "mean": round(float(np.mean(values)), 6),
        "std": round(float(np.std(values)), 6),
        "min": round(float(np.min(values)), 6),
        "max": round(float(np.max(values)), 6),
        "median": round(float(np.median(values)), 6),
        "p5": round(float(np.percentile(values, 5)), 6),
        "p95": round(float(np.percentile(values, 95)), 6),
    }


def load_reference_predictions() -> np.ndarray | None:
    if not os.path.exists(REFERENCE_DATA_PATH):
        return None
    try:
        df = pd.read_csv(REFERENCE_DATA_PATH)
        fraud_rate = df["Class"].mean()
        reference_probs = np.random.beta(2, 50, size=min(5000, len(df)))
        reference_probs = np.where(df["Class"].values[:len(reference_probs)] == 1, np.random.beta(5, 2, size=min(5000, len(df))), reference_probs)
        return reference_probs
    except Exception:
        return None


def load_recent_predictions(window: int = 500) -> list[dict]:
    if not os.path.exists(PREDICTIONS_LOG):
        return []
    records = []
    with open(PREDICTIONS_LOG, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return records[-window:]


def log_predictions(predictions: list[dict]) -> None:
    ensure_dirs()
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with open(PREDICTIONS_LOG, "a") as f:
        for pred in predictions:
            record = {
                "timestamp": timestamp,
                "probability": pred.get("probability", 0),
                "prediction": pred.get("prediction", 0),
                "risk_level": pred.get("risk_level", "unknown"),
            }
            f.write(json.dumps(record) + "\n")


def detect_drift(reference: np.ndarray, current: np.ndarray) -> dict:
    psi = compute_psi(reference, current)
    ref_stats = compute_distribution_stats(reference)
    cur_stats = compute_distribution_stats(current)

    psi_threshold = 0.1
    significant_drift = psi > psi_threshold

    mean_shift = abs(cur_stats["mean"] - ref_stats["mean"])
    mean_shift_threshold = 0.05
    mean_shift_detected = mean_shift > mean_shift_threshold

    return {
        "psi": round(psi, 6),
        "psi_threshold": psi_threshold,
        "significant_drift": significant_drift,
        "mean_shift": round(float(mean_shift), 6),
        "mean_shift_detected": mean_shift_detected,
        "reference_stats": ref_stats,
        "current_stats": cur_stats,
    }


def compute_prediction_metrics(records: list[dict]) -> dict:
    if not records:
        return {}

    probabilities = [r["probability"] for r in records]
    predictions = [r["prediction"] for r in records]

    return {
        "sample_size": len(records),
        "avg_probability": round(float(np.mean(probabilities)), 6),
        "std_probability": round(float(np.std(probabilities)), 6),
        "fraud_rate": round(float(np.mean(predictions)), 6),
        "high_risk_count": sum(1 for p in probabilities if p >= 0.8),
        "medium_risk_count": sum(1 for p in probabilities if 0.3 <= p < 0.8),
        "low_risk_count": sum(1 for p in probabilities if p < 0.3),
        "distribution": compute_distribution_stats(np.array(probabilities)),
    }


def run_monitoring() -> dict:
    ensure_dirs()
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

    recent_records = load_recent_predictions(window=1000)
    pred_metrics = compute_prediction_metrics(recent_records)

    drift_result = None
    reference_probs = load_reference_predictions()
    if reference_probs is not None and recent_records:
        current_probs = np.array([r["probability"] for r in recent_records])
        drift_result = detect_drift(reference_probs, current_probs)

    alerts = []
    if drift_result:
        if drift_result["significant_drift"]:
            alerts.append({
                "type": "concept_drift",
                "severity": "high",
                "message": f"PSI={drift_result['psi']:.4f} exceeds threshold {drift_result['psi_threshold']}",
            })
        if drift_result["mean_shift_detected"]:
            alerts.append({
                "type": "distribution_shift",
                "severity": "medium",
                "message": f"Mean prediction shifted by {drift_result['mean_shift']:.4f}",
            })

    if pred_metrics.get("fraud_rate", 0) > 0.1:
        alerts.append({
            "type": "high_fraud_rate",
            "severity": "high",
            "message": f"Fraud rate {pred_metrics['fraud_rate']:.2%} exceeds 10% threshold",
        })

    monitor_report = {
        "timestamp": timestamp,
        "prediction_metrics": pred_metrics,
        "drift_detection": drift_result,
        "alerts": alerts,
        "status": "alert" if alerts else "healthy",
    }

    metrics_history = []
    if os.path.exists(METRICS_FILE):
        try:
            with open(METRICS_FILE, "r") as f:
                metrics_history = json.load(f)
        except (json.JSONDecodeError, ValueError):
            metrics_history = []

    metrics_history.append(monitor_report)
    metrics_history = metrics_history[-100:]

    with open(METRICS_FILE, "w") as f:
        json.dump(metrics_history, f, indent=2)

    return monitor_report


def main() -> None:
    print("=" * 60)
    print("Model Monitoring - Drift Detection")
    print("=" * 60)

    report = run_monitoring()

    print(f"\nTimestamp: {report['timestamp']}")
    print(f"Status: {report['status']}")

    if report["prediction_metrics"]:
        pm = report["prediction_metrics"]
        print(f"\nPrediction Metrics (last {pm.get('sample_size', 0)} predictions):")
        print(f"  Avg probability: {pm.get('avg_probability', 'N/A')}")
        print(f"  Fraud rate: {pm.get('fraud_rate', 'N/A')}")
        print(f"  High risk: {pm.get('high_risk_count', 0)}")
        print(f"  Medium risk: {pm.get('medium_risk_count', 0)}")
        print(f"  Low risk: {pm.get('low_risk_count', 0)}")

    if report["drift_detection"]:
        dd = report["drift_detection"]
        print(f"\nDrift Detection:")
        print(f"  PSI: {dd['psi']}")
        print(f"  Significant drift: {dd['significant_drift']}")
        print(f"  Mean shift: {dd['mean_shift']}")

    if report["alerts"]:
        print(f"\nAlerts ({len(report['alerts'])}):")
        for alert in report["alerts"]:
            print(f"  [{alert['severity'].upper()}] {alert['type']}: {alert['message']}")
    else:
        print("\nNo alerts.")

    print(f"\nMetrics saved to {METRICS_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()
