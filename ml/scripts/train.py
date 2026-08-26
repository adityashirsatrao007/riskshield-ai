import os
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score,
    confusion_matrix, precision_recall_curve
)
from imblearn.over_sampling import SMOTE
import joblib

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "transactions.csv")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models")


def load_data():
    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df)} transactions, fraud rate: {df['is_fraud'].mean():.2%}")
    return df


def feature_engineering(df):
    df = df.copy()

    amount_mean = df["amount"].mean()
    amount_std = df["amount"].std()
    df["amount_zscore"] = (df["amount"] - amount_mean) / (amount_std + 1e-8)
    df["amount_log"] = np.log1p(df["amount"])

    df["txn_to_avg_ratio"] = df["amount"] / (df["merchant_avg_ticket_size"] + 1)
    df["account_age_bucket"] = pd.cut(df["customer_account_age_days"], bins=[0, 7, 30, 90, 365, 9999], labels=False)
    df["txn_frequency"] = df["customer_total_transactions"] / (df["customer_account_age_days"] + 1)

    df["is_night"] = ((df["hour_of_day"] >= 22) | (df["hour_of_day"] <= 5)).astype(int)
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)

    df["risk_flags"] = (
        df["is_international"] +
        (1 - df["shipping_address_match"]) +
        df["device_fingerprint_reused"] +
        df["is_night"] +
        (df["amount_zscore"] > 2).astype(int) +
        (df["customer_account_age_days"] < 30).astype(int)
    )

    le_card = LabelEncoder()
    df["card_type_enc"] = le_card.fit_transform(df["card_type"])
    le_network = LabelEncoder()
    df["card_network_enc"] = le_network.fit_transform(df["card_network"])
    le_category = LabelEncoder()
    df["merchant_category_enc"] = le_category.fit_transform(df["merchant_category_code"])
    le_country = LabelEncoder()
    df["country_enc"] = le_country.fit_transform(df["country_code"])

    return df, {
        "amount_mean": float(amount_mean),
        "amount_std": float(amount_std),
        "label_encoders": {
            "card_type": le_card,
            "card_network": le_network,
            "merchant_category": le_category,
            "country": le_country,
        }
    }


FEATURES = [
    "amount", "amount_log", "amount_zscore", "hour_of_day", "day_of_week",
    "is_international", "customer_account_age_days", "customer_total_transactions",
    "merchant_avg_ticket_size", "shipping_address_match", "device_fingerprint_reused",
    "txn_to_avg_ratio", "account_age_bucket", "txn_frequency",
    "is_night", "is_weekend", "risk_flags",
    "card_type_enc", "card_network_enc", "merchant_category_enc", "country_enc"
]


def train(df, metadata):
    X = df[FEATURES].values
    y = df["is_fraud"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    smote = SMOTE(random_state=42, sampling_strategy=0.5)
    X_train_res, y_train_res = smote.fit_resample(X_train, y_train)
    print(f"After SMOTE: {len(X_train_res)} samples, fraud rate: {y_train_res.mean():.2%}")

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_res)
    X_test_scaled = scaler.transform(X_test)

    models = {
        "RandomForest": RandomForestClassifier(
            n_estimators=200, max_depth=12, min_samples_split=10,
            class_weight="balanced", random_state=42, n_jobs=-1
        ),
        "GradientBoosting": GradientBoostingClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.1,
            subsample=0.8, random_state=42
        ),
    }

    best_model = None
    best_name = None
    best_f1 = 0

    for name, model in models.items():
        model.fit(X_train_scaled, y_train_res)
        y_pred = model.predict(X_test_scaled)
        y_proba = model.predict_proba(X_test_scaled)[:, 1]

        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        auc = roc_auc_score(y_test, y_proba)
        cm = confusion_matrix(y_test, y_pred)

        print(f"\n{name}:")
        print(f"  Precision: {precision:.4f}")
        print(f"  Recall:    {recall:.4f}")
        print(f"  F1:        {f1:.4f}")
        print(f"  AUC-ROC:   {auc:.4f}")
        print(f"  Confusion: {cm.tolist()}")

        if f1 > best_f1:
            best_f1 = f1
            best_model = model
            best_name = name

    print(f"\nBest model: {best_name} (F1={best_f1:.4f})")

    y_pred_best = best_model.predict(X_test_scaled)
    y_proba_best = best_model.predict_proba(X_test_scaled)[:, 1]
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred_best).ravel()

    avg_txn_value = df["amount"].mean()
    false_positive_cost = fp * avg_txn_value
    missed_fraud_cost = fn * avg_txn_value
    true_savings = tp * avg_txn_value

    precision_arr, recall_arr, thresholds = precision_recall_curve(y_test, y_proba_best)
    optimal_idx = np.argmax(2 * precision_arr * recall_arr / (precision_arr + recall_arr + 1e-8))
    optimal_threshold = float(thresholds[min(optimal_idx, len(thresholds) - 1)])

    feature_importances = {}
    importances = best_model.feature_importances_
    for feat, imp in sorted(zip(FEATURES, importances), key=lambda x: -x[1]):
        feature_importances[feat] = round(float(imp), 4)

    metrics = {
        "model_name": best_name,
        "precision": round(float(precision_score(y_test, y_pred_best)), 4),
        "recall": round(float(recall_score(y_test, y_pred_best)), 4),
        "f1_score": round(float(best_f1), 4),
        "auc_roc": round(float(roc_auc_score(y_test, y_proba_best)), 4),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "optimal_threshold": round(optimal_threshold, 4),
        "false_positive_cost_analysis": {
            "average_transaction_value": round(float(avg_txn_value), 2),
            "false_positives": int(fp),
            "total_fp_cost": round(float(false_positive_cost), 2),
            "missed_fraud_cost": round(float(missed_fraud_cost), 2),
            "true_savings": round(float(true_savings), 2),
            "net_benefit": round(float(true_savings - false_positive_cost), 2),
        },
        "feature_importances": feature_importances,
        "training_samples": int(len(X_train_res)),
        "test_samples": int(len(X_test)),
    }

    return best_model, scaler, metadata, metrics, optimal_threshold


if __name__ == "__main__":
    os.makedirs(MODEL_DIR, exist_ok=True)

    df = load_data()
    df, metadata = feature_engineering(df)
    model, scaler, metadata, metrics, threshold = train(df, metadata)

    joblib.dump({
        "model": model,
        "scaler": scaler,
        "metadata": metadata,
        "threshold": threshold,
        "features": FEATURES,
    }, os.path.join(MODEL_DIR, "fraud_detector.joblib"))

    with open(os.path.join(MODEL_DIR, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    with open(os.path.join(MODEL_DIR, "feature_importances.json"), "w") as f:
        json.dump(metrics["feature_importances"], f, indent=2)

    print(f"\nModel saved to {MODEL_DIR}/fraud_detector.joblib")
    print(f"Metrics saved to {MODEL_DIR}/metrics.json")
    print(f"Optimal threshold: {threshold:.4f}")
