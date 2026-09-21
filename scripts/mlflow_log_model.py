"""Log the RiskShield v2 model to MLflow for experiment tracking."""
import json
import mlflow
import mlflow.sklearn
from pathlib import Path

MLFLOW_URI = "http://mlflow:5000"
MODEL_PATH = Path(__file__).parent.parent / "models" / "fraud_detector_v2.joblib"
METRICS_PATH = Path(__file__).parent.parent / "models" / "metrics_v2.json"


def main():
    mlflow.set_tracking_uri(MLFLOW_URI)
    mlflow.set_experiment("RiskShield Fraud Detection v2")

    with METRICS_PATH.open() as f:
        metrics = json.load(f)

    with mlflow.start_run(run_name="fraud_detector_v2_production"):
        # Log parameters
        mlflow.log_param("model_type", metrics["model_name"])
        mlflow.log_param("n_features", 34)
        mlflow.log_param("optimal_threshold", metrics["optimal_threshold"])
        mlflow.log_param("training_samples", metrics["training_samples"])
        mlflow.log_param("test_samples", metrics["test_samples"])

        # Log metrics
        mlflow.log_metric("precision", metrics["precision"])
        mlflow.log_metric("recall", metrics["recall"])
        mlflow.log_metric("f1_score", metrics["f1_score"])
        mlflow.log_metric("auc_roc", metrics["auc_roc"])

        # Log confusion matrix
        cm = metrics["confusion_matrix"]
        mlflow.log_metric("true_negatives", cm["tn"])
        mlflow.log_metric("false_positives", cm["fp"])
        mlflow.log_metric("false_negatives", cm["fn"])
        mlflow.log_metric("true_positives", cm["tp"])

        # Log cost analysis
        cost = metrics["cost_analysis"]
        mlflow.log_metric("avg_transaction_value", cost["avg_transaction_value"])
        mlflow.log_metric("false_positive_cost", cost["false_positive_cost"])
        mlflow.log_metric("missed_fraud_cost", cost["missed_fraud_cost"])
        mlflow.log_metric("true_savings", cost["true_savings"])

        # Log feature importances as parameters (top 10)
        for feat, imp in list(metrics["feature_importances"].items())[:10]:
            mlflow.log_param(f"feat_imp_{feat}", round(imp, 4))

        # Log the model artifact
        mlflow.log_artifact(str(MODEL_PATH), artifact_path="model")

        print(f"MLflow run logged: {mlflow.active_run().info.run_id}")
        print(f"  F1={metrics['f1_score']}, AUC={metrics['auc_roc']}")
        print(f"  Precision={metrics['precision']}, Recall={metrics['recall']}")


if __name__ == "__main__":
    main()
