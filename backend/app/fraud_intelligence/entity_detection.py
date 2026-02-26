"""
InsureGuard AI - Entity Detection Module
Detects suspicious repeated entities across claims.
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from collections import Counter

from app.models.claim import Claim
from app.models.user import User


def detect_repeated_entities(db: Session) -> Dict[str, Any]:
    """
    Detect suspicious repeated entities across claims:
    - Same phone number used in multiple accounts
    - Same repair shop / hospital appearing frequently
    - Same address used in multiple claims
    """
    results = {
        "repeated_phones": [],
        "repeated_repair_shops": [],
        "repeated_hospitals": [],
        "repeated_addresses": [],
        "total_suspicious_entities": 0
    }

    # Repeated phone numbers
    phone_counts = db.query(User.phone, func.count(User.id)).filter(
        User.phone.isnot(None)
    ).group_by(User.phone).having(func.count(User.id) > 1).all()

    for phone, count in phone_counts:
        results["repeated_phones"].append({
            "phone": phone,
            "account_count": count,
            "risk": "high" if count > 3 else "medium"
        })

    # Repeated repair shops
    shop_counts = db.query(
        Claim.repair_shop_name, func.count(Claim.id)
    ).filter(
        Claim.repair_shop_name.isnot(None)
    ).group_by(Claim.repair_shop_name).having(func.count(Claim.id) > 2).all()

    for shop, count in shop_counts:
        results["repeated_repair_shops"].append({
            "shop_name": shop,
            "claim_count": count,
            "risk": "high" if count > 5 else "medium"
        })

    # Repeated hospitals
    hosp_counts = db.query(
        Claim.hospital_name, func.count(Claim.id)
    ).filter(
        Claim.hospital_name.isnot(None)
    ).group_by(Claim.hospital_name).having(func.count(Claim.id) > 3).all()

    for hosp, count in hosp_counts:
        results["repeated_hospitals"].append({
            "hospital_name": hosp,
            "claim_count": count,
            "risk": "high" if count > 7 else "medium"
        })

    # Repeated addresses (incident locations)
    addr_counts = db.query(
        Claim.incident_location, func.count(Claim.id)
    ).filter(
        Claim.incident_location.isnot(None)
    ).group_by(Claim.incident_location).having(func.count(Claim.id) > 2).all()

    for addr, count in addr_counts:
        results["repeated_addresses"].append({
            "address": addr,
            "claim_count": count,
            "risk": "high" if count > 4 else "medium"
        })

    results["total_suspicious_entities"] = (
        len(results["repeated_phones"]) +
        len(results["repeated_repair_shops"]) +
        len(results["repeated_hospitals"]) +
        len(results["repeated_addresses"])
    )

    return results
