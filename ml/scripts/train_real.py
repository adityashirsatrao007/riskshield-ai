import os
import json
import datetime
import warnings
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score,
    confusion_matrix, precision_recall_curve,
)
from imblearn.over_sampling import SMOTE

warnings.filterwarnings("ignore")

try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

try:
    import lightgbm as lgb
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False

try:
    import mlflow
    import mlflow.sklearn
    HAS_MLFLOW = True
except ImportError:
    HAS_MLFLOW = False

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(SCRIPT_DIR, "..", "data", "creditcard.csv")
MODEL_DIR = os.path.join(SCRIPT_DIR, "..", "models")
MODEL_PATH = os.path.join(MODEL_DIR, "fraud_detector_v2.joblib")
METRICS_PATH = os.path.join(MODEL_DIR, "metrics_v2.json")

FEATURE_COLS = [f"V{i}" for i in range(1, 29)] + ["Time", "Amount"]


def load_creditcard_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df)} rows, columns: {list(df.columns)}")
    class_dist = df["Class"].value_counts().to_dict()
    fraud_rate = df["Class"].mean()
    print(f"Class distribution: {class_dist}, fraud rate: {fraud_rate:.4%}")
    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    amount_mean = df["Amount"].mean()
    amount_std = df["Amount"].std()

    df["amount_log"] = np.log1p(df["Amount"])
    df["amount_zscore"] = (df["Amount"] - amount_mean) / (amount_std + 1e-8)
    df["hour_of_day"] = (df["Time"] % 86400) / 3600.0
    high_threshold = df["Amount"].quantile(0.95)
    df["is_high_amount"] = (df["Amount"] > high_threshold).astype(int)

    return df, {"amount_mean": float(amount_mean), "amount_std": float(amount_std), "high_amount_threshold": float(high_threshold)}


def get_feature_matrix(df: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    engineered = ["amount_log", "amount_zscore", "hour_of_day", "is_high_amount"]
    feature_names = FEATURE_COLS + engineered
    X = df[feature_names].values
    return X, feature_names


def build_models() -> dict[str, object]:
    models: dict[str, object] = {
        "RandomForest": RandomForestClassifier(
            n_estimators=300, max_depth=15, min_samples_split=5,
            class_weight="balanced", random_state=42, n_jobs=-1,
        ),
        "LogisticRegression": LogisticRegression(
            max_iter=1000, class_weight="balanced", random_state=42,
            solver="lbfgs", C=0.1,
        ),
    }
    if HAS_XGBOOST:
        models["XGBoost"] = xgb.XGBClassifier(
            n_estimators=300, max_depth=8, learning_rate=0.05,
            scale_pos_weight=10, subsample=0.8, colsample_bytree=0.8,
            random_state=42, eval_metric="logloss", n_jobs=-1,
        )
    if HAS_LIGHTGBM:
        models["LightGBM"] = lgb.LGBMClassifier(
            n_estimators=300, max_depth=8, learning_rate=0.05,
            scale_pos_weight=10, subsample=0.8, colsample_bytree=0.8,
            random_state=42, n_jobs=-1, verbose=-1,
        )
    available = list(models.keys())
    print(f"Models available: {available}")
    return models


def find_optimal_threshold(y_true: np.ndarray, y_proba: np.ndarray) -> float:
    precision_arr, recall_arr, thresholds = precision_recall_curve(y_true, y_proba)
    with np.errstate(divide="ignore", invalid="ignore"):
        f1_scores = 2 * precision_arr * recall_arr / (precision_arr + recall_arr + 1e-8)
    best_idx = int(np.argmax(f1_scores))
    if best_idx < len(thresholds):
        return float(thresholds[best_idx])
    return 0.5


def train_and_evaluate(
    X_train: np.ndarray, X_test: np.ndarray,
    y_train: np.ndarray, y_test: np.ndarray,
    feature_names: list[str], meta: dict,
) -> tuple[object, StandardScaler, dict]:
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    smote = SMOTE(random_state=42, sampling_strategy=0.3)
    X_train_res, y_train_res = smote.fit_resample(X_train_scaled, y_train)
    print(f"After SMOTE: {len(X_train_res)} samples, fraud rate: {y_train_res.mean():.2%}")

    models = build_models()
    results: list[dict] = []
    best_model = None
    best_name = ""
    best_f1 = -1.0

    experiment_run_id = None
    experiment_id = None
    if HAS_MLFLOW:
        try:
            mlflow.set_tracking_uri("file:./mlruns")
            experiment = mlflow.set_experiment("fraud-detection-real")
            experiment_id = experiment.experiment_id
        except Exception:
            pass

    for name, model in models.items():
        print(f"\nTraining {name}...")
        model.fit(X_train_res, y_train_res)
        y_pred = model.predict(X_test_scaled)
        y_proba = model.predict_proba(X_test_scaled)[:, 1]

        precision = float(precision_score(y_test, y_pred, zero_division=0))
        recall = float(recall_score(y_test, y_pred, zero_division=0))
        f1 = float(f1_score(y_test, y_pred, zero_division=0))
        auc = float(roc_auc_score(y_test, y_proba))
        threshold = find_optimal_threshold(y_test, y_proba)
        cm = confusion_matrix(y_test, y_pred)
        tn, fp, fn, tp = cm.ravel()

        result = {
            "model_name": name,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "auc_roc": round(auc, 4),
            "threshold": round(threshold, 4),
            "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        }
        results.append(result)
        print(f"  {name}: P={precision:.4f} R={recall:.4f} F1={f1:.4f} AUC={auc:.4f} Thresh={threshold:.4f}")

        if HAS_MLFLOW and experiment_id is not None:
            try:
                with mlflow.start_run(experiment_id=experiment_id, run_name=name):
                    mlflow.log_params(model.get_params() if hasattr(model, "get_params") else {})
                    mlflow.log_metrics({"precision": precision, "recall": recall, "f1": f1, "auc_roc": auc, "threshold": threshold})
                    mlflow.log_param("model_name", name)
                    mlflow.log_param("dataset_size", len(X_train) + len(X_test))
                    mlflow.log_param("smote_ratio", "0.3")
            except Exception:
                pass

        if f1 > best_f1:
            best_f1 = f1
            best_model = model
            best_name = name

    print(f"\nBest model: {best_name} (F1={best_f1:.4f})")

    y_pred_best = best_model.predict(X_test_scaled)
    y_proba_best = best_model.predict_proba(X_test_scaled)[:, 1]
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred_best).ravel()

    threshold_best = find_optimal_threshold(y_test, y_proba_best)

    feature_importances = {}
    if hasattr(best_model, "feature_importances_"):
        importances = best_model.feature_importances_
        for feat, imp in sorted(zip(feature_names, importances), key=lambda x: -x[1]):
            feature_importances[feat] = round(float(imp), 4)
    elif hasattr(best_model, "coef_"):
        coefs = np.abs(best_model.coef_[0])
        for feat, imp in sorted(zip(feature_names, coefs), key=lambda x: -x[1]):
            feature_importances[feat] = round(float(imp), 4)

    avg_amount = meta.get("amount_mean", 0)
    metrics = {
        "model_name": best_name,
        "precision": round(float(precision_score(y_test, y_pred_best, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred_best, zero_division=0)), 4),
        "f1_score": round(best_f1, 4),
        "auc_roc": round(float(roc_auc_score(y_test, y_proba_best)), 4),
        "optimal_threshold": round(threshold_best, 4),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "cost_analysis": {
            "avg_transaction_value": round(avg_amount, 2),
            "false_positive_cost": round(float(fp * avg_amount), 2),
            "missed_fraud_cost": round(float(fn * avg_amount), 2),
            "true_savings": round(float(tp * avg_amount), 2),
        },
        "feature_importances": feature_importances,
        "all_model_results": results,
        "training_samples": int(len(X_train_res)),
        "test_samples": int(len(X_test)),
    }

    return best_model, scaler, metrics


def save_model_bundle(model: object, scaler: StandardScaler, feature_names: list[str], meta: dict, metrics: dict) -> None:
    os.makedirs(MODEL_DIR, exist_ok=True)

    bundle = {
        "model": model,
        "scaler": scaler,
        "threshold": metrics["optimal_threshold"],
        "feature_names": feature_names,
        "metadata": {
            "training_date": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "dataset": "creditcard.csv",
            "dataset_size": meta["dataset_size"],
            "class_distribution": meta["class_distribution"],
            "fraud_rate": meta["fraud_rate"],
            "model_type": metrics["model_name"],
            "version": "2.0.0",
        },
    }

    joblib.dump(bundle, MODEL_PATH)
    print(f"Model bundle saved to {MODEL_PATH}")

    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"Metrics saved to {METRICS_PATH}")


def main() -> None:
    print("=" * 60)
    print("Fraud Detection - Real Data Training Pipeline")
    print("=" * 60)

    df = load_creditcard_data()
    df, feature_meta = engineer_features(df)

    X, feature_names = get_feature_matrix(df)
    y = df["Class"].values

    print(f"\nFeature matrix shape: {X.shape}")
    print(f"Features: {feature_names}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42,
    )
    print(f"\nTrain: {len(X_train)} | Test: {len(X_test)}")
    print(f"Train fraud rate: {y_train.mean():.4%} | Test fraud rate: {y_test.mean():.4%}")

    class_0 = int((y == 0).sum())
    class_1 = int((y == 1).sum())
    dataset_meta = {
        "dataset_size": len(df),
        "class_distribution": {0: class_0, 1: class_1},
        "fraud_rate": round(float(y.mean()), 6),
        "amount_mean": feature_meta["amount_mean"],
        "amount_std": feature_meta["amount_std"],
        "high_amount_threshold": feature_meta["high_amount_threshold"],
    }

    best_model, scaler, metrics = train_and_evaluate(
        X_train, X_test, y_train, y_test, feature_names, dataset_meta,
    )

    save_model_bundle(best_model, scaler, feature_names, dataset_meta, metrics)

    print("\n" + "=" * 60)
    print("Training complete.")
    print(f"  Model: {metrics['model_name']}")
    print(f"  F1:    {metrics['f1_score']}")
    print(f"  AUC:   {metrics['auc_roc']}")
    print(f"  Thresh: {metrics['optimal_threshold']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
