import os
import json
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, f1_score, confusion_matrix

from src.feature_engineering import FeatureEngineer, FEATURE_COLUMNS

class MLVerificationModel:
    def __init__(self, models_dir: Optional[str] = None):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.models_dir = models_dir or os.path.join(base_dir, "models")
        os.makedirs(self.models_dir, exist_ok=True)

        self.model_path = os.path.join(self.models_dir, "certificate_verification_model.pkl")
        self.preprocessor_path = os.path.join(self.models_dir, "preprocessor.pkl")
        self.config_path = os.path.join(self.models_dir, "feature_config.json")

        self.feature_engineer = FeatureEngineer()
        self.model = None
        self.preprocessor = None
        self.classes_ = ["INVALID", "NEEDS REVIEW", "VALID"]
        self.metrics_ = {}

        self.load_model()

    def generate_synthetic_training_data(self) -> pd.DataFrame:
        """
        Synthesizes a realistic training dataset covering all institutional verification scenarios:
        1. Valid external + OOD
        2. Valid internal + PRESENT / HOLIDAY
        3. Invalid external + Casual Leave
        4. Invalid external + Emergency Leave
        5. Invalid external + Unpaid Leave / Loss of pay
        6. Invalid external + Vacation
        7. Multi-day FDP with one conflicting day
        8. Unmatched faculty
        9. Missing entire attendance month
        10. Missing individual required attendance date
        11. Timeline mismatch (claimed != actual)
        12. Valid multi-day FDP with weekends (Holiday)
        """
        rows = []

        # 1. Valid External + OOD (Multi-day & single day)
        for d in [1, 2, 3, 5, 7, 10, 14]:
            for rep in range(15):
                holidays = max(0, d // 7 * 2)
                oods = d - holidays
                rows.append({
                    "is_internal": 0, "duration_days": d, "claimed_days": d, "timeline_match": 1,
                    "faculty_matched": 1, "cert_details_completeness": 1.0,
                    "ood_count": oods, "present_count": 0, "holiday_count": holidays,
                    "casual_leave_count": 0, "emergency_leave_count": 0, "unpaid_leave_count": 0,
                    "vacation_count": 0, "conflict_days_count": 0, "missing_days_count": 0,
                    "is_month_missing": 0, "attendance_coverage": 1.0, "label": "VALID"
                })

        # 2. Valid Internal + PRESENT (Multi-day & single day)
        for d in [1, 2, 5, 6, 10]:
            for rep in range(15):
                holidays = max(0, d // 7 * 2)
                presents = d - holidays
                rows.append({
                    "is_internal": 1, "duration_days": d, "claimed_days": d, "timeline_match": 1,
                    "faculty_matched": 1, "cert_details_completeness": 1.0,
                    "ood_count": 0, "present_count": presents, "holiday_count": holidays,
                    "casual_leave_count": 0, "emergency_leave_count": 0, "unpaid_leave_count": 0,
                    "vacation_count": 0, "conflict_days_count": 0, "missing_days_count": 0,
                    "is_month_missing": 0, "attendance_coverage": 1.0, "label": "VALID"
                })

        # 3. Invalid External + Casual Leave conflict
        for d in [1, 2, 3, 5]:
            for rep in range(12):
                rows.append({
                    "is_internal": 0, "duration_days": d, "claimed_days": d, "timeline_match": 1,
                    "faculty_matched": 1, "cert_details_completeness": 1.0,
                    "ood_count": max(0, d - 1), "present_count": 0, "holiday_count": 0,
                    "casual_leave_count": 1, "emergency_leave_count": 0, "unpaid_leave_count": 0,
                    "vacation_count": 0, "conflict_days_count": 1, "missing_days_count": 0,
                    "is_month_missing": 0, "attendance_coverage": 1.0, "label": "INVALID"
                })

        # 4. Invalid External + Emergency Leave conflict
        for d in [2, 5]:
            for rep in range(10):
                rows.append({
                    "is_internal": 0, "duration_days": d, "claimed_days": d, "timeline_match": 1,
                    "faculty_matched": 1, "cert_details_completeness": 1.0,
                    "ood_count": d - 1, "present_count": 0, "holiday_count": 0,
                    "casual_leave_count": 0, "emergency_leave_count": 1, "unpaid_leave_count": 0,
                    "vacation_count": 0, "conflict_days_count": 1, "missing_days_count": 0,
                    "is_month_missing": 0, "attendance_coverage": 1.0, "label": "INVALID"
                })

        # 5. Invalid External + Unpaid Leave conflict
        for d in [2, 5]:
            for rep in range(10):
                rows.append({
                    "is_internal": 0, "duration_days": d, "claimed_days": d, "timeline_match": 1,
                    "faculty_matched": 1, "cert_details_completeness": 1.0,
                    "ood_count": d - 1, "present_count": 0, "holiday_count": 0,
                    "casual_leave_count": 0, "emergency_leave_count": 0, "unpaid_leave_count": 1,
                    "vacation_count": 0, "conflict_days_count": 1, "missing_days_count": 0,
                    "is_month_missing": 0, "attendance_coverage": 1.0, "label": "INVALID"
                })

        # 6. Invalid External + Vacation conflict
        for d in [5, 12]:
            for rep in range(10):
                rows.append({
                    "is_internal": 0, "duration_days": d, "claimed_days": d, "timeline_match": 1,
                    "faculty_matched": 1, "cert_details_completeness": 1.0,
                    "ood_count": 0, "present_count": 0, "holiday_count": 0,
                    "casual_leave_count": 0, "emergency_leave_count": 0, "unpaid_leave_count": 0,
                    "vacation_count": d, "conflict_days_count": d, "missing_days_count": 0,
                    "is_month_missing": 0, "attendance_coverage": 1.0, "label": "INVALID"
                })

        # 7. Multi-day FDP with one conflicting day (OOD, OOD, Casual Leave)
        for rep in range(15):
            rows.append({
                "is_internal": 0, "duration_days": 3, "claimed_days": 3, "timeline_match": 1,
                "faculty_matched": 1, "cert_details_completeness": 1.0,
                "ood_count": 2, "present_count": 0, "holiday_count": 0,
                "casual_leave_count": 1, "emergency_leave_count": 0, "unpaid_leave_count": 0,
                "vacation_count": 0, "conflict_days_count": 1, "missing_days_count": 0,
                "is_month_missing": 0, "attendance_coverage": 1.0, "label": "INVALID"
            })

        # 8. Timeline Mismatch (claimed != actual)
        for rep in range(15):
            rows.append({
                "is_internal": 0, "duration_days": 5, "claimed_days": 2, "timeline_match": 0,
                "faculty_matched": 1, "cert_details_completeness": 0.8,
                "ood_count": 5, "present_count": 0, "holiday_count": 0,
                "casual_leave_count": 0, "emergency_leave_count": 0, "unpaid_leave_count": 0,
                "vacation_count": 0, "conflict_days_count": 0, "missing_days_count": 0,
                "is_month_missing": 0, "attendance_coverage": 1.0, "label": "INVALID"
            })

        # 9. External FDP but recorded PRESENT on campus (Conflict)
        for rep in range(12):
            rows.append({
                "is_internal": 0, "duration_days": 2, "claimed_days": 2, "timeline_match": 1,
                "faculty_matched": 1, "cert_details_completeness": 1.0,
                "ood_count": 0, "present_count": 2, "holiday_count": 0,
                "casual_leave_count": 0, "emergency_leave_count": 0, "unpaid_leave_count": 0,
                "vacation_count": 0, "conflict_days_count": 2, "missing_days_count": 0,
                "is_month_missing": 0, "attendance_coverage": 1.0, "label": "INVALID"
            })

        # 10. Missing Attendance Month -> NEEDS REVIEW
        for d in [1, 3, 5]:
            for rep in range(15):
                rows.append({
                    "is_internal": 0, "duration_days": d, "claimed_days": d, "timeline_match": 1,
                    "faculty_matched": 1, "cert_details_completeness": 1.0,
                    "ood_count": 0, "present_count": 0, "holiday_count": 0,
                    "casual_leave_count": 0, "emergency_leave_count": 0, "unpaid_leave_count": 0,
                    "vacation_count": 0, "conflict_days_count": 0, "missing_days_count": d,
                    "is_month_missing": 1, "attendance_coverage": 0.0, "label": "NEEDS REVIEW"
                })

        # 11. Month exists but individual date missing -> NEEDS REVIEW
        for rep in range(15):
            rows.append({
                "is_internal": 0, "duration_days": 3, "claimed_days": 3, "timeline_match": 1,
                "faculty_matched": 1, "cert_details_completeness": 1.0,
                "ood_count": 2, "present_count": 0, "holiday_count": 0,
                "casual_leave_count": 0, "emergency_leave_count": 0, "unpaid_leave_count": 0,
                "vacation_count": 0, "conflict_days_count": 0, "missing_days_count": 1,
                "is_month_missing": 0, "attendance_coverage": 0.67, "label": "NEEDS REVIEW"
            })

        # 12. Faculty Not Found -> NEEDS REVIEW
        for rep in range(15):
            rows.append({
                "is_internal": 0, "duration_days": 2, "claimed_days": 2, "timeline_match": 1,
                "faculty_matched": 0, "cert_details_completeness": 0.5,
                "ood_count": 0, "present_count": 0, "holiday_count": 0,
                "casual_leave_count": 0, "emergency_leave_count": 0, "unpaid_leave_count": 0,
                "vacation_count": 0, "conflict_days_count": 0, "missing_days_count": 2,
                "is_month_missing": 0, "attendance_coverage": 0.0, "label": "NEEDS REVIEW"
            })

        df = pd.DataFrame(rows)
        return df

    def train_and_evaluate(self, save_dataset_path: Optional[str] = None):
        """
        Trains and evaluates classification models, selects the best performing model,
        and saves artifacts to models/ directory.
        """
        df = self.generate_synthetic_training_data()
        if save_dataset_path:
            df.to_csv(save_dataset_path, index=False)

        X = df[FEATURE_COLUMNS]
        y = df["label"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.25, random_state=42, stratify=y
        )

        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        candidates = {
            "RandomForest": RandomForestClassifier(n_estimators=100, random_state=42),
            "GradientBoosting": GradientBoostingClassifier(n_estimators=100, random_state=42),
            "DecisionTree": DecisionTreeClassifier(random_state=42),
            "LogisticRegression": LogisticRegression(max_iter=500, random_state=42)
        }

        best_score = -1.0
        best_name = None
        best_model = None

        results = {}
        for name, clf in candidates.items():
            clf.fit(X_train_scaled, y_train)
            preds = clf.predict(X_test_scaled)
            acc = accuracy_score(y_test, preds)
            f1 = f1_score(y_test, preds, average='weighted')
            report = classification_report(y_test, preds, output_dict=True)
            cm = confusion_matrix(y_test, preds, labels=clf.classes_).tolist()

            results[name] = {
                "accuracy": round(acc, 4),
                "f1_score": round(f1, 4),
                "confusion_matrix": cm,
                "classes": clf.classes_.tolist(),
                "report": report
            }

            if f1 > best_score:
                best_score = f1
                best_name = name
                best_model = clf

        # Save chosen model & preprocessor
        self.model = best_model
        self.preprocessor = scaler
        self.classes_ = best_model.classes_.tolist()
        self.metrics_ = results

        joblib.dump(self.model, self.model_path)
        joblib.dump(self.preprocessor, self.preprocessor_path)

        config_data = {
            "best_model_name": best_name,
            "feature_columns": FEATURE_COLUMNS,
            "classes": self.classes_,
            "metrics": results
        }
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2)

        return results

    def load_model(self):
        """
        Loads saved model, preprocessor, and configuration.
        """
        if os.path.exists(self.model_path) and os.path.exists(self.preprocessor_path):
            try:
                self.model = joblib.load(self.model_path)
                self.preprocessor = joblib.load(self.preprocessor_path)
                if hasattr(self.model, 'classes_'):
                    self.classes_ = self.model.classes_.tolist()
            except Exception:
                self.model = None

        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    self.metrics_ = cfg.get("metrics", {})
            except Exception:
                pass

    def predict(self, feature_dict: Dict[str, float]) -> Dict[str, Any]:
        """
        Runs ML inference given extracted feature dictionary.
        Returns:
            - prediction: 'VALID', 'INVALID', or 'NEEDS REVIEW'
            - confidence: float confidence score (0.0 to 1.0)
            - probabilities: dict of class -> probability
        """
        if self.model is None or self.preprocessor is None:
            # Automatic fallback: initialize and train model on first run
            self.train_and_evaluate()

        X_df = self.feature_engineer.to_dataframe([feature_dict])
        X_scaled = self.preprocessor.transform(X_df)

        pred_class = self.model.predict(X_scaled)[0]
        probs = {}
        confidence = 0.0

        if hasattr(self.model, "predict_proba"):
            prob_arr = self.model.predict_proba(X_scaled)[0]
            for cls_name, p in zip(self.classes_, prob_arr):
                probs[cls_name] = round(float(p), 4)
            confidence = float(max(prob_arr))
        else:
            probs[pred_class] = 1.0
            confidence = 1.0

        return {
            "prediction": pred_class,
            "confidence": round(confidence, 4),
            "probabilities": probs
        }
