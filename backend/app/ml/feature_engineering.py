"""
InsureGuard AI - Feature Engineering Module
Creates fraud-detection features for each insurance category.
"""

import numpy as np
from datetime import datetime, timezone
from typing import Dict, Any, Optional


def compute_claim_to_premium_ratio(claim_amount: float, premium_amount: Optional[float]) -> float:
    """Ratio of claim to premium — high ratios are suspicious."""
    if not premium_amount or premium_amount <= 0:
        return 5.0  # Default high ratio if unknown premium
    return min(claim_amount / premium_amount, 50.0)


def compute_time_since_policy_start(policy_start_date: Optional[datetime],
                                     incident_date: Optional[datetime]) -> float:
    """Days between policy start and incident — very short = suspicious."""
    if not policy_start_date or not incident_date:
        return 180  # Default to 6 months
    delta = (incident_date - policy_start_date).days
    return max(delta, 0)


def compute_claim_frequency(user_claims_count: int) -> int:
    """Number of claims filed by same user — high frequency = suspicious."""
    return user_claims_count


def compute_suspicious_amount_flag(claim_amount: float, category: str) -> int:
    """Flag unusually high claim amounts per category."""
    thresholds = {
        "vehicle": 500000,   # 5 Lakh
        "health": 1000000,   # 10 Lakh
        "property": 2000000  # 20 Lakh
    }
    threshold = thresholds.get(category, 1000000)
    return 1 if claim_amount > threshold else 0


def compute_incident_severity(description: str) -> float:
    """Encode incident severity based on keywords (0-1 scale)."""
    severe_words = ["total loss", "fire", "flood", "theft", "stolen", "fatal",
                    "critical", "icu", "surgery", "collapsed", "destroyed"]
    moderate_words = ["accident", "damage", "injury", "broken", "crack",
                      "hospitalized", "fracture", "leak"]
    minor_words = ["scratch", "dent", "minor", "consultation", "checkup"]

    desc_lower = description.lower()
    severe_count = sum(1 for w in severe_words if w in desc_lower)
    moderate_count = sum(1 for w in moderate_words if w in desc_lower)
    minor_count = sum(1 for w in minor_words if w in desc_lower)

    if severe_count > 0:
        return min(0.7 + severe_count * 0.1, 1.0)
    elif moderate_count > 0:
        return min(0.3 + moderate_count * 0.1, 0.7)
    elif minor_count > 0:
        return max(0.1, 0.3 - minor_count * 0.05)
    return 0.5


def compute_location_risk(location: Optional[str]) -> float:
    """Location-based fraud risk scoring (0-1) based on known high-risk areas."""
    if not location:
        return 0.5

    # Simulated high-risk locations (in production, use actual fraud data)
    high_risk_keywords = ["mumbai", "delhi", "noida", "gurgaon", "bangalore",
                          "hyderabad", "pune", "chennai", "kolkata"]
    loc_lower = location.lower()

    for keyword in high_risk_keywords:
        if keyword in loc_lower:
            return 0.7
    return 0.3


def compute_repair_shop_repetition(repair_shop_name: Optional[str],
                                     known_shops: dict) -> int:
    """Detect if repair shop appears repeatedly across claims."""
    if not repair_shop_name:
        return 0
    return known_shops.get(repair_shop_name.lower().strip(), 0)


def compute_weekend_holiday_flag(incident_date: Optional[datetime]) -> int:
    """Flag incidents on weekends or common holidays."""
    if not incident_date:
        return 0
    return 1 if incident_date.weekday() >= 5 else 0


def compute_late_reporting_flag(incident_date: Optional[datetime],
                                  created_at: Optional[datetime]) -> int:
    """Flag claims filed significantly after the incident."""
    if not incident_date or not created_at:
        return 0
    delta = (created_at - incident_date).days
    return 1 if delta > 30 else 0


def extract_features(claim_data: Dict[str, Any],
                      user_claims_count: int = 0,
                      known_repair_shops: dict = None) -> Dict[str, float]:
    """
    Extract all fraud-detection features from a claim.
    Returns a dictionary of feature names to values.
    """
    if known_repair_shops is None:
        known_repair_shops = {}

    category = claim_data.get("insurance_category", "vehicle")

    features = {
        "claim_amount": float(claim_data.get("claim_amount", 0)),
        "premium_amount": float(claim_data.get("premium_amount", 0) or 0),
        "claim_to_premium_ratio": compute_claim_to_premium_ratio(
            float(claim_data.get("claim_amount", 0)),
            claim_data.get("premium_amount")
        ),
        "time_since_policy_start": compute_time_since_policy_start(
            claim_data.get("policy_start_date"),
            claim_data.get("incident_date")
        ),
        "claim_frequency": compute_claim_frequency(user_claims_count),
        "suspicious_amount_flag": compute_suspicious_amount_flag(
            float(claim_data.get("claim_amount", 0)), category
        ),
        "incident_severity": compute_incident_severity(
            claim_data.get("incident_description", "")
        ),
        "location_risk": compute_location_risk(
            claim_data.get("incident_location")
        ),
        "weekend_holiday_flag": compute_weekend_holiday_flag(
            claim_data.get("incident_date")
        ),
        "late_reporting_flag": compute_late_reporting_flag(
            claim_data.get("incident_date"),
            claim_data.get("created_at")
        ),
    }

    # Category-specific features
    if category == "vehicle":
        features["repair_shop_repetition"] = compute_repair_shop_repetition(
            claim_data.get("repair_shop_name"), known_repair_shops
        )
        features["is_vehicle_claim"] = 1
        features["is_health_claim"] = 0
        features["is_property_claim"] = 0

    elif category == "health":
        # Hospital stay duration
        admission = claim_data.get("admission_date")
        discharge = claim_data.get("discharge_date")
        if admission and discharge:
            stay_days = (discharge - admission).days
            features["hospital_stay_days"] = max(stay_days, 0)
        else:
            features["hospital_stay_days"] = 0

        features["repair_shop_repetition"] = 0
        features["is_vehicle_claim"] = 0
        features["is_health_claim"] = 1
        features["is_property_claim"] = 0

    elif category == "property":
        features["repair_shop_repetition"] = 0
        features["is_vehicle_claim"] = 0
        features["is_health_claim"] = 0
        features["is_property_claim"] = 1

    return features


def get_feature_names() -> list:
    """Get ordered list of feature names for model input."""
    return [
        "claim_amount", "premium_amount", "claim_to_premium_ratio",
        "time_since_policy_start", "claim_frequency",
        "suspicious_amount_flag", "incident_severity", "location_risk",
        "weekend_holiday_flag", "late_reporting_flag",
        "repair_shop_repetition",
        "is_vehicle_claim", "is_health_claim", "is_property_claim"
    ]
