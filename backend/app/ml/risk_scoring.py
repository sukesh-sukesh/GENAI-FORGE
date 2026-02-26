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


def get_model():
    """Get cached model, loading if necessary."""
    global _model, _scaler, _metadata
    if _model is None:
        _model, _scaler, _metadata = load_model()
    return _model, _scaler, _metadata


def predict_fraud_risk(
    claim_data: Dict[str, Any],
    user_claims_count: int = 0,
    known_repair_shops: dict = None
) -> Dict[str, Any]:
    """
    Predict fraud risk for a claim.
    Returns fraud probability, risk score, risk category, and top factors.
    """
    model, scaler, metadata = get_model()

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

    # Risk category
    if fraud_probability < FRAUD_THRESHOLD_LOW:
        risk_category = "low"
    elif fraud_probability < FRAUD_THRESHOLD_HIGH:
        risk_category = "medium"
    else:
        risk_category = "high"

    # Top contributing factors
    fraud_factors = compute_top_factors(features, metadata)

    return {
        "fraud_probability": round(fraud_probability, 4),
        "risk_score": risk_score,
        "risk_category": risk_category,
        "fraud_factors": fraud_factors,
        "optimal_threshold": optimal_threshold,
        "features_used": features
    }


def compute_top_factors(features: Dict[str, float],
                         metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Compute top contributing fraud factors using feature importance.
    Returns top 5 factors with their names, values, and contribution scores.
    """
    importances = metadata.get("feature_importances", {})
    if not importances:
        return []

    # Calculate contribution = feature_value * feature_importance
    contributions = []
    for fname, fval in features.items():
        imp = importances.get(fname, 0)
        contribution = abs(float(fval) * float(imp))
        contributions.append({
            "feature": fname,
            "value": round(float(fval), 4),
            "importance": round(float(imp), 4),
            "contribution": round(contribution, 4),
            "description": get_feature_description(fname)
        })

    # Sort by contribution and return top 5
    contributions.sort(key=lambda x: x["contribution"], reverse=True)
    return contributions[:5]


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
    model, scaler, metadata = get_model()
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
