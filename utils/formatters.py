"""
Data Formatting Utilities

This module provides formatting utilities for insurance form processing:
- JSON response formatting
- Data structure conversion
- Display formatting for Streamlit
- Error message formatting

Technology: Python data formatting and JSON handling
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional


class InsuranceFormatter:
    """Formatter class for insurance data and responses"""

    def __init__(self):
        self.date_format = "%Y-%m-%d"
        self.display_date_format = "%B %d, %Y"
        self.currency_symbol = "$"

    def format_currency(self, amount: Optional[float]) -> str:
        """Format monetary amount for display"""
        if amount is None:
            return "N/A"
        try:
            return f"{self.currency_symbol}{amount:,.2f}"
        except (ValueError, TypeError):
            return "Invalid amount"

    def format_date_for_display(self, date_string: Optional[str]) -> str:
        """Format date for user-friendly display"""
        if not date_string:
            return "N/A"
        try:
            date_obj = datetime.strptime(date_string, self.date_format)
            return date_obj.strftime(self.display_date_format)
        except ValueError:
            return date_string

    def format_insurance_data_for_display(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Format insurance data for Streamlit display"""
        formatted = {
            "Policy Number": data.get("policy_number", "N/A"),
            "Policy Holder Name": data.get("policy_holder_name", "N/A"),
            "Age": str(data.get("age", "N/A")) if data.get("age") is not None else "N/A",
            "Address": data.get("address", "N/A"),
            "Beneficiary": data.get("beneficiary", "N/A"),
            "Date of Birth": self.format_date_for_display(data.get("date_of_birth")),
            "Policy Start Date": self.format_date_for_display(data.get("policy_start_date")),
            "Policy End Date": self.format_date_for_display(data.get("policy_end_date")),
            "Premium Amount": self.format_currency(data.get("premium_amount")),
            "Coverage Amount": self.format_currency(data.get("coverage_amount")),
        }
        return formatted

    def format_validation_results(self, validation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format validation results for display"""
        return {
            "status": "passed" if not validation_data.get("validation_errors") else "failed",
            "error_count": len(validation_data.get("validation_errors", [])),
            "warning_count": len(validation_data.get("validation_warnings", [])),
            "errors": validation_data.get("validation_errors", []),
            "warnings": validation_data.get("validation_warnings", []),
        }

    def format_processing_summary(self, final_response: Dict[str, Any]) -> Dict[str, Any]:
        """Format processing summary for dashboard display"""
        summary = final_response.get("summary", {})
        return {
            "Processing Status": final_response.get("processing_status", "Unknown").replace("_", " ").title(),
            "Data Completeness": f"{summary.get('data_completeness', 0)}%",
            "Processing Confidence": f"{summary.get('processing_confidence', 0)}%",
            "Total Errors": summary.get("total_errors", 0),
            "Total Warnings": summary.get("total_warnings", 0),
            "Business Flags": summary.get("business_flags_count", 0),
            "Processing Time": self._format_timestamp(final_response.get("processing_timestamp")),
        }

    def format_quality_assessment(self, quality_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Format quality assessment data for display"""
        return {
            "Validation Errors": quality_data.get("validation_errors", []),
            "Validation Warnings": quality_data.get("validation_warnings", []),
            "Sanity Errors": quality_data.get("sanity_errors", []),
            "Sanity Warnings": quality_data.get("sanity_warnings", []),
            "Business Flags": quality_data.get("business_flags", []),
        }

    def format_step_output(self, step_name: str, output_data: Any) -> Dict[str, Any]:
        """Format individual step output for display"""
        formatted = {
            "step": step_name.replace("_", " ").title(),
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "status": "completed",
            "output": output_data
        }

        if step_name == "ocr":
            formatted["preview"] = str(output_data)[:200] + "..." if len(str(output_data)) > 200 else str(output_data)
        elif step_name == "language":
            formatted["detected_language"] = output_data
        elif step_name in ["mapping", "validation", "sanity", "response"]:
            try:
                if isinstance(output_data, str):
                    formatted["parsed_output"] = json.loads(output_data)
            except json.JSONDecodeError:
                formatted["raw_output"] = str(output_data)

        return formatted

    def create_download_data(self, final_response: Dict[str, Any]) -> Dict[str, Any]:
        """Create formatted data for download"""
        return {
            "processing_info": {
                "timestamp": final_response.get("processing_timestamp"),
                "status": final_response.get("processing_status"),
                "system_version": "1.0.0"
            },
            "extracted_data": final_response.get("extracted_data", {}),
            "quality_metrics": final_response.get("summary", {}),
            "quality_details": final_response.get("quality_assessment", {})
        }

    def _format_timestamp(self, timestamp_str: Optional[str]) -> str:
        """Format ISO timestamp for display"""
        if not timestamp_str:
            return "N/A"
        try:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, AttributeError):
            return timestamp_str


# Create global formatter instance
insurance_formatter = InsuranceFormatter()
