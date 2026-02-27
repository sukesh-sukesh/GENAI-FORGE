"""
InsureGuard AI - Model Training Module
Trains and compares multiple models for fraud detection.
Includes cost-sensitive learning and threshold optimization.
"""

import numpy as np
import pandas as pd
import joblib
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Tuple, Optional
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (roc_auc_score, precision_recall_curve, f1_score,
                              recall_score, precision_score, classification_report,
                              confusion_matrix)
from sklearn.utils.class_weight import compute_class_weight

try:
    from xgboost import XGBClassifier
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

try:
    from imblearn.over_sampling import SMOTE
    HAS_SMOTE = True
except ImportError:
    HAS_SMOTE = False

from app.config import ML_MODELS_DIR, FALSE_NEGATIVE_COST, FALSE_POSITIVE_COST
from app.ml.feature_engineering import get_feature_names


def generate_synthetic_training_data(n_samples: int = 5000) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Generate synthetic training data for fraud detection.
    In production, replace with actual historical claims data.
    Creates realistic feature distributions with ~15% fraud rate.
    """
    np.random.seed(42)

    n_fraud = int(n_samples * 0.15)
    n_legit = n_samples - n_fraud

    feature_names = get_feature_names()

    # Generate legitimate claims
    legit_data = {
        "claim_amount": np.random.lognormal(10, 1.5, n_legit).clip(1000, 5000000),
        "premium_amount": np.random.lognormal(8, 1, n_legit).clip(500, 200000),
        "claim_to_premium_ratio": np.random.exponential(2, n_legit).clip(0.1, 10),
        "time_since_policy_start": np.random.exponential(365, n_legit).clip(30, 3650),
        "claim_frequency": np.random.poisson(1, n_legit).clip(0, 5),
        "suspicious_amount_flag": np.random.binomial(1, 0.05, n_legit),
        "incident_severity": np.random.beta(2, 5, n_legit),
        "location_risk": np.random.beta(3, 7, n_legit),
        "weekend_holiday_flag": np.random.binomial(1, 0.28, n_legit),
        "late_reporting_flag": np.random.binomial(1, 0.05, n_legit),
        "repair_shop_repetition": np.random.poisson(0.5, n_legit).clip(0, 10),
        "is_vehicle_claim": np.random.binomial(1, 0.4, n_legit),
        "is_health_claim": np.random.binomial(1, 0.35, n_legit),
        "is_property_claim": np.random.binomial(1, 0.25, n_legit),
    }

    # Generate fraudulent claims (different distributions)
    fraud_data = {
        "claim_amount": np.random.lognormal(11, 2, n_fraud).clip(5000, 10000000),
        "premium_amount": np.random.lognormal(7.5, 0.8, n_fraud).clip(500, 100000),
        "claim_to_premium_ratio": np.random.exponential(5, n_fraud).clip(1, 50),
        "time_since_policy_start": np.random.exponential(60, n_fraud).clip(5, 365),
        "claim_frequency": np.random.poisson(3, n_fraud).clip(1, 15),
        "suspicious_amount_flag": np.random.binomial(1, 0.45, n_fraud),
        "incident_severity": np.random.beta(5, 2, n_fraud),
        "location_risk": np.random.beta(6, 3, n_fraud),
        "weekend_holiday_flag": np.random.binomial(1, 0.55, n_fraud),
        "late_reporting_flag": np.random.binomial(1, 0.35, n_fraud),
        "repair_shop_repetition": np.random.poisson(3, n_fraud).clip(0, 20),
        "is_vehicle_claim": np.random.binomial(1, 0.5, n_fraud),
        "is_health_claim": np.random.binomial(1, 0.3, n_fraud),
        "is_property_claim": np.random.binomial(1, 0.2, n_fraud),
    }

    legit_df = pd.DataFrame(legit_data)
    fraud_df = pd.DataFrame(fraud_data)

    X = pd.concat([legit_df, fraud_df], ignore_index=True)
    y = pd.Series([0] * n_legit + [1] * n_fraud)

    # Shuffle
    shuffle_idx = np.random.permutation(len(X))
    X = X.iloc[shuffle_idx].reset_index(drop=True)
    y = y.iloc[shuffle_idx].reset_index(drop=True)

    return X, y


def compute_optimal_threshold(y_true: np.ndarray, y_proba: np.ndarray) -> float:
    """
    Find optimal classification threshold using cost-sensitive analysis.
    Minimizes total business cost = FN_cost * num_FN + FP_cost * num_FP
    """
    best_threshold = 0.5
    min_cost = float("inf")

    for threshold in np.arange(0.1, 0.9, 0.01):
        y_pred = (y_proba >= threshold).astype(int)
        cm = confusion_matrix(y_true, y_pred)
        tn, fp, fn, tp = cm.ravel()

        total_cost = (fn * FALSE_NEGATIVE_COST) + (fp * FALSE_POSITIVE_COST)
        if total_cost < min_cost:
            min_cost = total_cost
            best_threshold = threshold

    return round(best_threshold, 2)


def train_and_compare_models(X: pd.DataFrame = None, y: pd.Series = None) -> Dict[str, Any]:
    """
    Train multiple models, compare them, and select the best one.
    Returns training results and saves the best model.
    """
    if X is None or y is None:
        X, y = generate_synthetic_training_data()

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Apply SMOTE if available
    if HAS_SMOTE:
        smote = SMOTE(random_state=42)
        X_train_resampled, y_train_resampled = smote.fit_resample(X_train_scaled, y_train)
    else:
        X_train_resampled, y_train_resampled = X_train_scaled, y_train

    # Compute class weights
    classes = np.unique(y_train)
    weights = compute_class_weight("balanced", classes=classes, y=y_train)
    class_weights = dict(zip(classes, weights))

    # Define models
    models = {
        "logistic_regression": LogisticRegression(
            class_weight="balanced", max_iter=1000, random_state=42
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=100, class_weight="balanced",
            max_depth=10, random_state=42, n_jobs=-1
        ),
        "gradient_boosting": GradientBoostingClassifier(
            n_estimators=100, max_depth=5,
            learning_rate=0.1, random_state=42
        ),
    }

    if HAS_XGBOOST:
        models["xgboost"] = XGBClassifier(
            n_estimators=100, max_depth=5,
            learning_rate=0.1, scale_pos_weight=class_weights.get(1, 1),
            random_state=42, use_label_encoder=False,
            eval_metric="logloss"
        )

    results = {}
    best_model_name = None
    best_auc = 0

    for name, model in models.items():
        print(f"Training {name}...")

        # Train
        model.fit(X_train_resampled, y_train_resampled)

        # Predict
        y_pred = model.predict(X_test_scaled)
        y_proba = model.predict_proba(X_test_scaled)[:, 1]

        # Metrics
        auc = roc_auc_score(y_test, y_proba)
        f1 = f1_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)

        # Optimal threshold
        opt_threshold = compute_optimal_threshold(y_test.values, y_proba)
        
        # Cross-validation score
        cv_scores = cross_val_score(model, X_train_resampled, y_train_resampled, cv=5, scoring="roc_auc")

        # PR Curve
        precisions, recalls, _ = precision_recall_curve(y_test, y_proba)
        
        # Format PR Curve data for frontend (keep 20 points for visualization)
        n_points = 20
        idx = np.linspace(0, len(precisions) - 1, n_points, dtype=int)
        
        pr_curve = {
            "precision": precisions[idx].tolist(),
            "recall": recalls[idx].tolist()
        }

        # Confusion Matrix
        y_pred_opt = (y_proba >= opt_threshold).astype(int)
        cm = confusion_matrix(y_test, y_pred_opt).tolist()

        results[name] = {
            "roc_auc": round(auc, 4),
            "f1_score": round(f1, 4),
            "recall": round(recall, 4),
            "precision": round(precision, 4),
            "optimal_threshold": opt_threshold,
            "cv_auc_mean": round(cv_scores.mean(), 4),
            "cv_auc_std": round(cv_scores.std(), 4),
            "confusion_matrix": cm,
            "pr_curve": pr_curve
        }

        print(f"  AUC: {auc:.4f}, F1: {f1:.4f}, Recall: {recall:.4f}")

        if auc > best_auc:
            best_auc = auc
            best_model_name = name

    # Save best model
    best_model = models[best_model_name]
    model_path = ML_MODELS_DIR / "fraud_model.joblib"
    scaler_path = ML_MODELS_DIR / "scaler.joblib"
    metadata_path = ML_MODELS_DIR / "model_metadata.json"

    joblib.dump(best_model, model_path)
    joblib.dump(scaler, scaler_path)

    # Feature importances
    if hasattr(best_model, "feature_importances_"):
        importances = dict(zip(get_feature_names(), best_model.feature_importances_.tolist()))
    elif hasattr(best_model, "coef_"):
        importances = dict(zip(get_feature_names(), np.abs(best_model.coef_[0]).tolist()))
    else:
        importances = {}

    metadata = {
        "best_model": best_model_name,
        "metrics": results[best_model_name],
        "all_results": results,
        "feature_importances": importances,
        "optimal_threshold": results[best_model_name]["optimal_threshold"],
        "trained_at": datetime.now().isoformat(),
        "n_train_samples": len(X_train_resampled),
        "n_test_samples": len(X_test),
        "smote_applied": HAS_SMOTE,
        "feature_names": get_feature_names()
    }

    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    # Train Isolation Forest for Anomaly Score
    from sklearn.ensemble import IsolationForest
    print("Training Isolation Forest...")
    iso_forest = IsolationForest(contamination=0.15, random_state=42)
    iso_forest.fit(X_train_resampled)
    joblib.dump(iso_forest, ML_MODELS_DIR / "isolation_forest.joblib")

    print(f"\n[BEST] Best model: {best_model_name} (AUC: {best_auc:.4f})")
    print(f"   Saved to: {model_path}")

    return metadata


def load_model():
    """Load the trained model, scaler, and metadata."""
    model_path = ML_MODELS_DIR / "fraud_model.joblib"
    scaler_path = ML_MODELS_DIR / "scaler.joblib"
    metadata_path = ML_MODELS_DIR / "model_metadata.json"

    if not model_path.exists():
        print("No trained model found. Training new model...")
        train_and_compare_models()

    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)

    with open(metadata_path) as f:
        metadata = json.load(f)

    return model, scaler, metadata


if __name__ == "__main__":
    results = train_and_compare_models()
    print("\n=== Training Results ===")
    for name, metrics in results["all_results"].items():
        print(f"\n{name}:")
        for k, v in metrics.items():
            print(f"  {k}: {v}")
