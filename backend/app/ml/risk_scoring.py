"""
InsureGuard AI - Risk Scoring Engine
Converts model predictions into actionable risk assessments.
"""

import numpy as np
from typing import Dict, Any, List, Optional
from app.ml.feature_engineering import extract_features, get_feature_names
from app.ml.model_training import load_model
from app.config import FRAUD_THRESHOLD_LOW, FRAUD_THRESHOLD_HIGH


# Cached model components
_model = None
_scaler = None
_metadata = None
_iso_forest = None


def get_model():
    """Get cached model, loading if necessary."""
    global _model, _scaler, _metadata, _iso_forest
    if _model is None:
        _model, _scaler, _metadata = load_model()
        import joblib
        from app.config import ML_MODELS_DIR
        iso_path = ML_MODELS_DIR / "isolation_forest.joblib"
        if iso_path.exists():
            _iso_forest = joblib.load(iso_path)
    return _model, _scaler, _metadata, _iso_forest


def predict_fraud_risk(
    claim_data: Dict[str, Any],
    user_claims_count: int = 0,
    known_repair_shops: dict = None,
    fraud_threshold: float = 0.70
) -> Dict[str, Any]:
    """
    Predict fraud risk for a claim.
    Returns fraud probability, risk score, risk category, and top factors.
    """
    model, scaler, metadata, iso_forest = get_model()

    # Extract features
    features = extract_features(claim_data, user_claims_count, known_repair_shops)
    feature_names = get_feature_names()

    # Ensure all features are present and ordered
    feature_vector = []
    for name in feature_names:
        val = features.get(name, 0)
        # Handle None and NaN
        if val is None or (isinstance(val, float) and np.isnan(val)):
            val = 0
        feature_vector.append(float(val))

    feature_array = np.array([feature_vector])

    # Scale features
    feature_scaled = scaler.transform(feature_array)

    # Predict probability
    fraud_probability = float(model.predict_proba(feature_scaled)[0][1])

    # Apply optimal threshold from training
    optimal_threshold = metadata.get("optimal_threshold", 0.5)

    # Risk score (0-100)
    risk_score = round(fraud_probability * 100, 1)

    # Risk category based on adaptive threshold
    if fraud_probability >= fraud_threshold:
        risk_category = "high"
    elif fraud_probability >= fraud_threshold * 0.5:
        risk_category = "medium"
    else:
        risk_category = "low"

    # Top contributing factors
    fraud_factors = compute_top_factors(features, metadata)

    # Anomaly score
    anomaly_score = 0.0
    if iso_forest is not None:
        # iso_forest.predict returns 1 for normal, -1 for anomaly
        iso_pred = iso_forest.predict(feature_scaled)[0]
        anomaly_score = float((1 - iso_pred) / 2) # 0.0 = normal, 1.0 = anomaly

    return {
        "fraud_probability": round(fraud_probability, 4),
        "risk_score": risk_score,
        "risk_category": risk_category,
        "fraud_factors": fraud_factors,
        "optimal_threshold": optimal_threshold,
        "features_used": features,
        "anomaly_score": anomaly_score
    }


def compute_top_factors(features: Dict[str, float],
                         metadata: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Compute top contributing fraud factors using feature importance.
    Returns positive and negative factors normalized as percentages.
    """
    importances = metadata.get("feature_importances", {})
    if not importances:
        return {"positive_factors": [], "negative_factors": []}

    positive_contributions = []
    negative_contributions = []
    total_abs_contribution = 0.0

    raw_contributions = []
    for fname, fval in features.items():
        imp = importances.get(fname, 0)
        # Assuming importance * value gives direction and magnitude
        contribution = float(fval) * float(imp)
        if contribution != 0:
            raw_contributions.append({
                "feature": fname,
                "value": round(float(fval), 4),
                "importance": round(float(imp), 4),
                "contribution": contribution,
                "description": get_feature_description(fname)
            })
            total_abs_contribution += abs(contribution)

    if total_abs_contribution == 0:
        return {"positive_factors": [], "negative_factors": []}

    for item in raw_contributions:
        contribution = item["contribution"]
        weight_pct = (abs(contribution) / total_abs_contribution) * 100
        result_item = {
            "feature": item["feature"],
            "value": item["value"],
            "contribution": round(contribution, 4),
            "weight_pct": round(weight_pct, 1),
            "description": item["description"]
        }
        if contribution > 0:
            positive_contributions.append(result_item)
        else:
            negative_contributions.append(result_item)

    # Sort by absolute magnitude
    positive_contributions.sort(key=lambda x: x["weight_pct"], reverse=True)
    negative_contributions.sort(key=lambda x: x["weight_pct"], reverse=True)

    return {
        "positive_factors": positive_contributions[:5],
        "negative_factors": negative_contributions[:5]
    }


def get_feature_description(feature_name: str) -> str:
    """Get human-readable description for a feature."""
    descriptions = {
        "claim_amount": "Claim amount is unusually high",
        "premium_amount": "Premium amount relative to claim",
        "claim_to_premium_ratio": "Claim-to-premium ratio exceeds normal range",
        "time_since_policy_start": "Policy is very new — claim filed shortly after purchase",
        "claim_frequency": "Multiple claims filed by the same policyholder",
        "suspicious_amount_flag": "Claim amount exceeds category threshold",
        "incident_severity": "Incident description indicates high severity",
        "location_risk": "Location associated with higher fraud rates",
        "weekend_holiday_flag": "Incident occurred on weekend/holiday",
        "late_reporting_flag": "Claim filed significantly after incident",
        "repair_shop_repetition": "Same repair shop linked to multiple claims",
        "is_vehicle_claim": "Vehicle insurance claim type",
        "is_health_claim": "Health insurance claim type",
        "is_property_claim": "Property insurance claim type",
        "hospital_stay_days": "Duration of hospital stay"
    }
    return descriptions.get(feature_name, feature_name.replace("_", " ").title())


def compute_shap_explanations(claim_data: Dict[str, Any],
                                user_claims_count: int = 0) -> Dict[str, Any]:
    """
    Compute SHAP-like feature importance explanations.
    Uses model's built-in feature importances as a proxy.
    """
    model, scaler, metadata, _ = get_model()
    features = extract_features(claim_data, user_claims_count)

    importances = metadata.get("feature_importances", {})

    # Create SHAP-like explanation
    explanations = {}
    for fname, fval in features.items():
        imp = importances.get(fname, 0)
        explanations[fname] = {
            "value": round(float(fval), 4),
            "impact": round(float(fval) * float(imp), 4),
            "direction": "increases_risk" if float(fval) * float(imp) > 0 else "decreases_risk",
            "description": get_feature_description(fname)
        }

    return explanations
