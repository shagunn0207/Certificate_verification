import os
from typing import Dict, Any, Optional
from src.data_loader import DataLoader
from src.certificate_processing import CertificateProcessor
from src.verification import RuleVerificationEngine
from src.feature_engineering import FeatureEngineer
from src.ml_model import MLVerificationModel
from src.history import VerificationHistoryManager

class VerificationPipeline:
    def __init__(self, data_dir: Optional[str] = None):
        self.data_loader = DataLoader(data_dir=data_dir)
        self.cert_processor = CertificateProcessor(self.data_loader)
        self.rule_engine = RuleVerificationEngine(self.data_loader)
        self.feature_engineer = FeatureEngineer()
        self.ml_model = MLVerificationModel()
        self.history_manager = VerificationHistoryManager()

    def verify_uploaded_certificate(
        self,
        file_bytes: bytes,
        filename: str,
        fallback_meta: Optional[Dict[str, Any]] = None,
        save_to_history: bool = True
    ) -> Dict[str, Any]:
        """
        Executes end-to-end verification for an uploaded file:
        File -> OCR -> Extraction -> Faculty Match -> Duplicate Check ->
        Attendance Lookup -> Rule Engine -> Feature Engineering -> ML Model ->
        Hybrid Result -> Audit History.
        """
        # 1 & 2. Process File & OCR
        cert_data = self.cert_processor.process_uploaded_file(
            file_bytes=file_bytes,
            filename=filename,
            fallback_meta=fallback_meta
        )

        # 3. Duplicate Check — before running the full pipeline
        if save_to_history:
            duplicate_record = self.history_manager.find_duplicate(cert_data)
            if duplicate_record:
                return {
                    "is_duplicate": True,
                    "cert_data": cert_data,
                    "duplicate_of": duplicate_record,
                    "final_result": "DUPLICATE",
                    "final_reason": "This certificate already exists in the system. No new record was added and counts were not increased.",
                    # Provide empty structures for UI compatibility
                    "rule_output": {},
                    "ml_output": {"prediction": "N/A", "confidence": 0.0, "probabilities": {}},
                    "features": {}
                }

        return self._execute_core_pipeline(cert_data, save_to_history=save_to_history)

    def verify_existing_certificate(
        self,
        tracker_row: Dict[str, Any],
        save_to_history: bool = True
    ) -> Dict[str, Any]:
        """
        Executes end-to-end verification for a certificate from certificate_tracker.csv.
        The original tracker row is treated as READ-ONLY; no fields are written back to it.
        """
        cert_data = self.cert_processor.process_existing_record(tracker_row)
        # Preserve the original tracker result for audit comparison (read-only reference)
        cert_data['TRACKER_ORIGINAL_RESULT'] = tracker_row.get('VERIFICATION RESULT', '').strip()

        # Duplicate Check for existing certificates too
        if save_to_history:
            duplicate_record = self.history_manager.find_duplicate(cert_data)
            if duplicate_record:
                return {
                    "is_duplicate": True,
                    "cert_data": cert_data,
                    "duplicate_of": duplicate_record,
                    "final_result": "DUPLICATE",
                    "final_reason": "This certificate already exists in the system. No new record was added and counts were not increased.",
                    "rule_output": {},
                    "ml_output": {"prediction": "N/A", "confidence": 0.0, "probabilities": {}},
                    "features": {}
                }

        return self._execute_core_pipeline(cert_data, save_to_history=save_to_history)

    def _execute_core_pipeline(self, cert_data: Dict[str, Any], save_to_history: bool = True) -> Dict[str, Any]:
        """
        Core verification logic combining Rule Engine and Machine Learning.
        """
        # 1. Rule Engine Verification
        rule_output = self.rule_engine.verify(cert_data)

        # 2. Feature Engineering
        features = self.feature_engineer.extract_features(cert_data, rule_output)

        # 3. Machine Learning Prediction
        ml_output = self.ml_model.predict(features)

        # 4. Hybrid Consensus & Final Result Formulation
        rule_result = rule_output["RULE_RESULT"]
        rule_reason = rule_output["RULE_REASON"]
        ml_pred = ml_output["prediction"]

        # Deterministic rules guarantee integrity:
        # A. Attendance conflicts / timeline mismatches CANNOT be silently overridden by ML
        if rule_result == "INVALID":
            final_result = "INVALID"
            final_reason = rule_reason

        # B. Missing attendance evidence / unmatched faculty MUST trigger human review
        elif rule_result == "NEEDS REVIEW":
            final_result = "NEEDS REVIEW"
            final_reason = rule_reason

        # C. Rule Engine verified valid
        elif rule_result == "VALID":
            if ml_pred == "VALID":
                final_result = "VALID"
                final_reason = rule_reason
            else:
                # ML detected anomaly in duration, pattern, or completeness
                final_result = "NEEDS REVIEW"
                final_reason = f"Attendance records match OOD/Present status, but ML model flagged anomaly (ML: {ml_pred} with {ml_output['confidence']*100:.1f}% confidence). Human review recommended."
        else:
            final_result = rule_result
            final_reason = rule_reason

        response = {
            "is_duplicate": False,
            "cert_data": cert_data,
            "rule_output": rule_output,
            "ml_output": ml_output,
            "features": features,
            "final_result": final_result,
            "final_reason": final_reason
        }

        # 5. Save to verification history (results/verification_results.csv) ONLY.
        #    NEVER write computed results back to the original certificate_tracker.csv.
        if save_to_history:
            history_record = self.history_manager.record_verification(
                cert_data=cert_data,
                rule_output=rule_output,
                ml_output=ml_output,
                final_result=final_result,
                final_reason=final_reason
            )
            response["history_record"] = history_record

        return response
