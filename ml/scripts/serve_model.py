import os
import datetime
import numpy as np
import joblib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(SCRIPT_DIR, "..", "models")
MODEL_PATH = os.path.join(MODEL_DIR, "fraud_detector_v2.joblib")

app = FastAPI(title="Fraud Detection Model Service", version="2.0.0")

_model_bundle = None


def load_model_bundle() -> dict:
    global _model_bundle
    if _model_bundle is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model not found at {MODEL_PATH}. Run train_real.py first.")
        _model_bundle = joblib.load(MODEL_PATH)
    return _model_bundle


class PredictionRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    features: dict[str, float] = Field(..., description="Feature name to value mapping")


class PredictionResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    probability: float
    prediction: int
    risk_level: str
    is_flagged: bool
    feature_importances: dict[str, float]
    model_version: str


class HealthResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    status: str
    model_loaded: bool
    timestamp: str


class ModelInfoResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    version: str
    model_type: str
    training_date: str
    dataset_size: int
    fraud_rate: float
    threshold: float
    feature_count: int
    feature_names: list[str]


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    model_loaded = _model_bundle is not None
    return HealthResponse(
        status="ok" if model_loaded else "model_not_loaded",
        model_loaded=model_loaded,
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    )


@app.get("/model-info", response_model=ModelInfoResponse)
def model_info() -> ModelInfoResponse:
    bundle = load_model_bundle()
    metadata = bundle["metadata"]
    return ModelInfoResponse(
        version=metadata.get("version", "unknown"),
        model_type=metadata.get("model_type", "unknown"),
        training_date=metadata.get("training_date", "unknown"),
        dataset_size=metadata.get("dataset_size", 0),
        fraud_rate=metadata.get("fraud_rate", 0.0),
        threshold=bundle["threshold"],
        feature_count=len(bundle["feature_names"]),
        feature_names=bundle["feature_names"],
    )


@app.post("/predict", response_model=PredictionResponse)
def predict(req: PredictionRequest) -> PredictionResponse:
    bundle = load_model_bundle()
    model = bundle["model"]
    scaler = bundle["scaler"]
    feature_names = bundle["feature_names"]
    threshold = bundle["threshold"]

    missing = set(feature_names) - set(req.features.keys())
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing features: {sorted(missing)}")

    feature_values = [req.features[f] for f in feature_names]
    X = np.array([feature_values])
    X_scaled = scaler.transform(X)

    proba = model.predict_proba(X_scaled)[0]
    fraud_prob = float(proba[1])
    prediction = int(fraud_prob >= threshold)

    if fraud_prob >= 0.8:
        risk_level = "critical"
    elif fraud_prob >= 0.6:
        risk_level = "high"
    elif fraud_prob >= 0.3:
        risk_level = "medium"
    else:
        risk_level = "low"

    importances: dict[str, float] = {}
    if hasattr(model, "feature_importances_"):
        for feat, imp in zip(feature_names, model.feature_importances_):
            importances[feat] = round(float(imp), 4)
    elif hasattr(model, "coef_"):
        for feat, imp in zip(feature_names, np.abs(model.coef_[0])):
            importances[feat] = round(float(imp), 4)

    return PredictionResponse(
        probability=round(fraud_prob, 6),
        prediction=prediction,
        risk_level=risk_level,
        is_flagged=prediction == 1,
        feature_importances=importances,
        model_version=bundle["metadata"].get("version", "unknown"),
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
