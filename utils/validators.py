"""
Validation Rules and Functions

This module provides validation utilities for insurance form data:
- Date format validation
- Numeric range validation
- Field presence validation
- Business rule validation helpers

Technology: Python validation logic with datetime and regex
"""

import re
from datetime import datetime, date
from typing import List, Dict, Any, Tuple


class InsuranceValidator:
    """Validator class for insurance form data"""

    def __init__(self):
        self.date_format = "%Y-%m-%d"
        self.required_fields = ["policy_number", "policy_holder_name"]
        self.numeric_fields = ["age", "premium_amount", "coverage_amount"]
        self.date_fields = ["date_of_birth", "policy_start_date", "policy_end_date"]

    def validate_date_format(self, date_string: str) -> Tuple[bool, str]:
        """Validate date format (YYYY-MM-DD)"""
        if not date_string:
            return False, "Date is empty"
        try:
            datetime.strptime(date_string, self.date_format)
            return True, "Valid date format"
        except ValueError:
            return False, f"Invalid date format. Expected YYYY-MM-DD, got: {date_string}"

    def validate_age(self, age: Any) -> Tuple[bool, str]:
        """Validate age value"""
        if age is None:
            return True, "Age is optional"
        try:
            age_num = float(age)
            if age_num < 0:
                return False, "Age cannot be negative"
            if age_num > 150:
                return False, "Age cannot exceed 150 years"
            if age_num != int(age_num):
                return False, "Age must be a whole number"
            return True, "Valid age"
        except (ValueError, TypeError):
            return False, f"Age must be a number, got: {type(age).__name__}"

    def validate_amount(self, amount: Any, field_name: str) -> Tuple[bool, str]:
        """Validate monetary amounts"""
        if amount is None:
            return True, f"{field_name} is optional"
        try:
            amount_num = float(amount)
            if amount_num < 0:
                return False, f"{field_name} cannot be negative"
            if amount_num > 10000000:
                return False, f"{field_name} exceeds maximum limit"
            return True, f"Valid {field_name}"
        except (ValueError, TypeError):
            return False, f"{field_name} must be a number, got: {type(amount).__name__}"

    def validate_policy_number(self, policy_number: str) -> Tuple[bool, str]:
        """Validate policy number format"""
        if not policy_number:
            return False, "Policy number is required"
        policy_number = policy_number.strip()
        if len(policy_number) < 3:
            return False, "Policy number too short (minimum 3 characters)"
        if len(policy_number) > 50:
            return False, "Policy number too long (maximum 50 characters)"
        if not re.match(r'^[A-Za-z0-9\-_]+$', policy_number):
            return False, "Policy number contains invalid characters"
        return True, "Valid policy number"

    def validate_name(self, name: str) -> Tuple[bool, str]:
        """Validate policy holder name"""
        if not name:
            return False, "Policy holder name is required"
        name = name.strip()
        if len(name) < 2:
            return False, "Name too short (minimum 2 characters)"
        if len(name) > 100:
            return False, "Name too long (maximum 100 characters)"
        if not re.match(r"^[A-Za-z\s\-'\.]+$", name):
            return False, "Name contains invalid characters"
        return True, "Valid name"

    def validate_all_fields(self, fields: Dict[str, Any]) -> Dict[str, List[str]]:
        """Validate all insurance fields"""
        errors = []
        warnings = []

        # Required fields
        for field in self.required_fields:
            if not fields.get(field):
                warnings.append(f"Missing required field: {field}")

        # Policy number
        if fields.get("policy_number"):
            is_valid, msg = self.validate_policy_number(fields["policy_number"])
            if not is_valid:
                errors.append(f"Policy number: {msg}")

        # Name
        if fields.get("policy_holder_name"):
            is_valid, msg = self.validate_name(fields["policy_holder_name"])
            if not is_valid:
                errors.append(f"Policy holder name: {msg}")

        # Age
        if fields.get("age") is not None:
            is_valid, msg = self.validate_age(fields["age"])
            if not is_valid:
                errors.append(f"Age: {msg}")

        # Dates
        for field in self.date_fields:
            if fields.get(field):
                is_valid, msg = self.validate_date_format(fields[field])
                if not is_valid:
                    errors.append(f"{field}: {msg}")

        # Amounts
        amount_fields = {
            "premium_amount": "Premium amount",
            "coverage_amount": "Coverage amount"
        }
        for field, label in amount_fields.items():
            if fields.get(field) is not None:
                is_valid, msg = self.validate_amount(fields[field], label)
                if not is_valid:
                    errors.append(f"{field}: {msg}")

        return {
            "errors": errors,
            "warnings": warnings
        }

    def validate_date_consistency(self, fields: Dict[str, Any]) -> List[str]:
        """Validate date consistency (age vs DOB, policy dates)"""
        errors = []

        # Age vs DOB
        if fields.get("age") and fields.get("date_of_birth"):
            try:
                dob = datetime.strptime(fields["date_of_birth"], self.date_format).date()
                today = date.today()
                calculated_age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                if abs(calculated_age - fields["age"]) > 1:
                    errors.append(
                        f"Age mismatch: Stated age {fields['age']}, calculated age {calculated_age}"
                    )
            except ValueError:
                pass  # already handled in date format validation

        # Policy start and end date
        if fields.get("policy_start_date") and fields.get("policy_end_date"):
            try:
                start = datetime.strptime(fields["policy_start_date"], self.date_format)
                end = datetime.strptime(fields["policy_end_date"], self.date_format)
                if end <= start:
                    errors.append("Policy end date must be after start date")
            except ValueError:
                pass  # already handled in date format validation

        return errors


# Global instance for use across agents
insurance_validator = InsuranceValidator()
