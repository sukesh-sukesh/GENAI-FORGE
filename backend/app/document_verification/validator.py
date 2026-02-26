"""
InsureGuard AI - Document Validator
Validates Indian insurance document formats:
- GST Number (GSTIN)
- Vehicle RC Number
- Hospital Registration Number
- Invoice Number Format
- Policy Number Format
"""

import re
from typing import Dict, Any, Optional, List


def validate_gst_number(gst: str) -> Dict[str, Any]:
    """
    Validate Indian GST Number (GSTIN) format.
    Format: 2-digit state code + 10-char PAN + entity number + Z + check digit
    Example: 22AAAAA0000A1Z5
    """
    pattern = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
    is_valid = bool(re.match(pattern, gst.upper().strip()))

    return {
        "field": "gst_number",
        "value": gst,
        "is_valid": is_valid,
        "format": "XX XXXXX 0000 X XZ X",
        "message": "Valid GSTIN format" if is_valid else "Invalid GSTIN format. Expected: 22AAAAA0000A1Z5"
    }


def validate_vehicle_rc_number(rc: str) -> Dict[str, Any]:
    """
    Validate Indian Vehicle Registration Certificate (RC) Number.
    Format: XX-00-XX-0000 (State-District-Series-Number)
    Examples: MH-12-AB-1234, DL-01-CA-5678
    """
    # Remove spaces and hyphens for flexible matching
    rc_clean = rc.upper().replace(" ", "").replace("-", "")
    pattern = r"^[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{1,4}$"
    is_valid = bool(re.match(pattern, rc_clean))

    return {
        "field": "rc_number",
        "value": rc,
        "is_valid": is_valid,
        "format": "XX-00-XX-0000",
        "message": "Valid RC number format" if is_valid else "Invalid RC format. Expected: MH-12-AB-1234"
    }


def validate_hospital_registration(reg: str) -> Dict[str, Any]:
    """
    Validate Hospital Registration Number.
    Common format: State abbreviation + numbers (varies by state).
    """
    pattern = r"^[A-Z]{2,5}[-/]?[0-9]{3,10}$"
    is_valid = bool(re.match(pattern, reg.upper().strip()))

    return {
        "field": "hospital_registration",
        "value": reg,
        "is_valid": is_valid,
        "format": "XX-XXXXXX",
        "message": "Valid hospital registration format" if is_valid else "Invalid hospital registration format"
    }


def validate_invoice_number(invoice: str) -> Dict[str, Any]:
    """
    Validate Invoice Number format.
    Common formats: INV-YYYY-XXXX, alphanumeric with dashes.
    """
    pattern = r"^[A-Z]{2,5}[-/]?[0-9]{4}[-/]?[A-Z0-9]{3,10}$"
    is_valid = bool(re.match(pattern, invoice.upper().strip()))

    return {
        "field": "invoice_number",
        "value": invoice,
        "is_valid": is_valid,
        "format": "INV-YYYY-XXXX",
        "message": "Valid invoice format" if is_valid else "Invalid invoice format"
    }


def validate_policy_number(policy: str) -> Dict[str, Any]:
    """
    Validate Insurance Policy Number.
    General format: Alphanumeric, typically 10-20 characters.
    """
    pattern = r"^[A-Z0-9]{5,25}$"
    policy_clean = policy.upper().replace(" ", "").replace("-", "").replace("/", "")
    is_valid = bool(re.match(pattern, policy_clean))

    return {
        "field": "policy_number",
        "value": policy,
        "is_valid": is_valid,
        "format": "Alphanumeric, 5-25 chars",
        "message": "Valid policy number format" if is_valid else "Invalid policy number format"
    }


def validate_aadhaar_number(aadhaar: str) -> Dict[str, Any]:
    """
    Validate Indian Aadhaar Number.
    Format: 12 digits, not starting with 0 or 1.
    """
    aadhaar_clean = aadhaar.replace(" ", "").replace("-", "")
    pattern = r"^[2-9]{1}[0-9]{11}$"
    is_valid = bool(re.match(pattern, aadhaar_clean))

    return {
        "field": "aadhaar_number",
        "value": aadhaar,
        "is_valid": is_valid,
        "format": "XXXX XXXX XXXX",
        "message": "Valid Aadhaar format" if is_valid else "Invalid Aadhaar format"
    }


def validate_pan_number(pan: str) -> Dict[str, Any]:
    """
    Validate Indian PAN Number.
    Format: AAAAA0000A (5 letters, 4 digits, 1 letter)
    """
    pattern = r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$"
    is_valid = bool(re.match(pattern, pan.upper().strip()))

    return {
        "field": "pan_number",
        "value": pan,
        "is_valid": is_valid,
        "format": "AAAAA0000A",
        "message": "Valid PAN format" if is_valid else "Invalid PAN format"
    }


def cross_check_amount(form_amount: float, document_amount: Optional[float],
                        tolerance: float = 0.05) -> Dict[str, Any]:
    """
    Cross-check claim amount from form vs. extracted from document.
    Allows tolerance for rounding differences.
    """
    if document_amount is None:
        return {
            "check": "amount_cross_check",
            "match": None,
            "message": "Could not extract amount from document"
        }

    diff = abs(form_amount - document_amount)
    threshold = form_amount * tolerance
    match = diff <= threshold

    return {
        "check": "amount_cross_check",
        "form_amount": form_amount,
        "document_amount": document_amount,
        "difference": round(diff, 2),
        "tolerance": f"{tolerance*100}%",
        "match": match,
        "message": "Amounts match within tolerance" if match else
                   f"Amount mismatch: Form ₹{form_amount:,.2f} vs Document ₹{document_amount:,.2f}"
    }


def validate_documents_for_category(category: str, documents: List[Dict],
                                      claim_data: Dict) -> Dict[str, Any]:
    """
    Validate all documents for a given insurance category.
    Returns comprehensive validation results.
    """
    results = {
        "category": category,
        "validations": [],
        "overall_score": 0,
        "issues": []
    }

    # Validate policy number
    policy_result = validate_policy_number(claim_data.get("policy_number", ""))
    results["validations"].append(policy_result)
    if not policy_result["is_valid"]:
        results["issues"].append("Invalid policy number format")

    # Category-specific validations
    if category == "vehicle":
        if claim_data.get("vehicle_number"):
            rc_result = validate_vehicle_rc_number(claim_data["vehicle_number"])
            results["validations"].append(rc_result)
            if not rc_result["is_valid"]:
                results["issues"].append("Invalid vehicle RC number")

    elif category == "health":
        if claim_data.get("hospital_registration_number"):
            hosp_result = validate_hospital_registration(
                claim_data["hospital_registration_number"]
            )
            results["validations"].append(hosp_result)
            if not hosp_result["is_valid"]:
                results["issues"].append("Invalid hospital registration number")

    # Calculate overall score
    valid_count = sum(1 for v in results["validations"] if v.get("is_valid"))
    total = len(results["validations"])
    results["overall_score"] = round((valid_count / total * 100) if total > 0 else 0, 1)

    return results
