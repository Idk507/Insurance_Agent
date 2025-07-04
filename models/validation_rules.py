"""
Validation Rule Definitions

Defines:
- Field validation rules
- Business rule checks
- Data consistency checks
- Custom validation logic

Tech: Pydantic + Custom Classes
"""

from datetime import date
from typing import List, Dict
from pydantic import BaseModel, Field
from enum import Enum


# ------------------------ Enums ------------------------

class ValidationSeverity(str, Enum):
    """Severity levels for validation feedback"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationRuleType(str, Enum):
    """Types of validation logic"""
    FORMAT = "format"
    RANGE = "range"
    REQUIRED = "required"
    BUSINESS = "business"
    CONSISTENCY = "consistency"


# ------------------------ Rule Model ------------------------

class ValidationRule(BaseModel):
    """Definition of a single validation rule"""
    rule_id: str
    field_name: str
    rule_type: ValidationRuleType
    severity: ValidationSeverity
    description: str
    error_message: str
    is_active: bool = True


# ------------------------ Rule Manager ------------------------

class FieldValidationRules:
    """Registry for field-based rules"""

    def __init__(self):
        self.rules: Dict[str, List[ValidationRule]] = self._initialize_rules()

    def _initialize_rules(self) -> Dict[str, List[ValidationRule]]:
        """Define validation rules per field"""
        rules = {
            "policy_number": [
                ValidationRule("policy_number_required", "policy_number", ValidationRuleType.REQUIRED,
                               ValidationSeverity.WARNING, "Must be present", "Policy number is missing"),
                ValidationRule("policy_number_format", "policy_number", ValidationRuleType.FORMAT,
                               ValidationSeverity.ERROR, "Must match format", "Policy number format is invalid"),
                ValidationRule("policy_number_length", "policy_number", ValidationRuleType.RANGE,
                               ValidationSeverity.ERROR, "Must be 3-50 characters", "Length must be between 3-50")
            ],
            "policy_holder_name": [
                ValidationRule("name_required", "policy_holder_name", ValidationRuleType.REQUIRED,
                               ValidationSeverity.WARNING, "Must be present", "Policy holder name is missing"),
                ValidationRule("name_format", "policy_holder_name", ValidationRuleType.FORMAT,
                               ValidationSeverity.ERROR, "Must be alphabetic", "Invalid characters in name"),
                ValidationRule("name_length", "policy_holder_name", ValidationRuleType.RANGE,
                               ValidationSeverity.ERROR, "Must be 2-100 characters", "Length must be 2-100")
            ],
            "age": [
                ValidationRule("age_range", "age", ValidationRuleType.RANGE,
                               ValidationSeverity.ERROR, "Must be between 0–150", "Age out of valid range"),
                ValidationRule("age_integer", "age", ValidationRuleType.FORMAT,
                               ValidationSeverity.ERROR, "Must be integer", "Age must be a whole number")
            ],
            "date_of_birth": [
                ValidationRule("dob_format", "date_of_birth", ValidationRuleType.FORMAT,
                               ValidationSeverity.ERROR, "Must match format", "DOB must be YYYY-MM-DD"),
                ValidationRule("dob_reasonable", "date_of_birth", ValidationRuleType.BUSINESS,
                               ValidationSeverity.ERROR, "Check reasonableness", "DOB seems invalid")
            ],
            "premium_amount": [
                ValidationRule("premium_positive", "premium_amount", ValidationRuleType.RANGE,
                               ValidationSeverity.ERROR, "Must be positive", "Premium must be positive"),
                ValidationRule("premium_reasonable", "premium_amount", ValidationRuleType.BUSINESS,
                               ValidationSeverity.WARNING, "Check bounds", "Premium seems high or low")
            ],
            "coverage_amount": [
                ValidationRule("coverage_positive", "coverage_amount", ValidationRuleType.RANGE,
                               ValidationSeverity.ERROR, "Must be positive", "Coverage must be positive"),
                ValidationRule("coverage_reasonable", "coverage_amount", ValidationRuleType.BUSINESS,
                               ValidationSeverity.WARNING, "Check bounds", "Coverage seems high or low")
            ],
            "policy_start_date": [
                ValidationRule("start_date_format", "policy_start_date", ValidationRuleType.FORMAT,
                               ValidationSeverity.ERROR, "Must match format", "Start date must be YYYY-MM-DD")
            ],
            "policy_end_date": [
                ValidationRule("end_date_format", "policy_end_date", ValidationRuleType.FORMAT,
                               ValidationSeverity.ERROR, "Must match format", "End date must be YYYY-MM-DD")
            ]
        }
        return rules

    def get_rules_for_field(self, field_name: str) -> List[ValidationRule]:
        return self.rules.get(field_name, [])

    def get_active_rules_for_field(self, field_name: str) -> List[ValidationRule]:
        return [r for r in self.get_rules_for_field(field_name) if r.is_active]

    def get_all_rules(self) -> List[ValidationRule]:
        all_rules = []
        for rule_list in self.rules.values():
            all_rules.extend(rule_list)
        return all_rules


# ------------------------ Business Rules ------------------------

class BusinessRules:
    """Business logic constraints"""

    MIN_AGE = 0
    MAX_AGE = 150
    MINOR_AGE_THRESHOLD = 18
    SENIOR_AGE_THRESHOLD = 65
    MIN_PREMIUM = 0
    MAX_PREMIUM = 1_000_000
    MIN_COVERAGE = 0
    MAX_COVERAGE = 100_000_000
    LOW_PREMIUM_THRESHOLD = 100
    HIGH_PREMIUM_THRESHOLD = 100_000
    MIN_COVERAGE_RATIO = 10
    MAX_COVERAGE_RATIO = 1000
    MAX_POLICY_DURATION_YEARS = 50

    @classmethod
    def validate_age_business_rules(cls, age: int) -> List[str]:
        flags = []
        if age < cls.MINOR_AGE_THRESHOLD:
            flags.append(f"Minor detected: Age {age}")
        elif age > cls.SENIOR_AGE_THRESHOLD:
            flags.append(f"Senior citizen: Age {age}")
        if age > 120:
            flags.append(f"Unrealistic age: {age}")
        return flags

    @classmethod
    def validate_premium_business_rules(cls, premium: float) -> List[str]:
        flags = []
        if premium < cls.LOW_PREMIUM_THRESHOLD:
            flags.append(f"Low premium: ${premium:,.2f}")
        elif premium > cls.HIGH_PREMIUM_THRESHOLD:
            flags.append(f"High premium: ${premium:,.2f}")
        return flags

    @classmethod
    def validate_coverage_ratio(cls, coverage: float, premium: float) -> List[str]:
        flags = []
        if premium > 0:
            ratio = coverage / premium
            if ratio > cls.MAX_COVERAGE_RATIO:
                flags.append(f"High coverage-to-premium ratio: {ratio:.1f}x")
            elif ratio < cls.MIN_COVERAGE_RATIO:
                flags.append(f"Low coverage-to-premium ratio: {ratio:.1f}x")
        return flags

    @classmethod
    def validate_policy_duration(cls, start: date, end: date) -> List[str]:
        flags = []
        if end <= start:
            flags.append("End date must be after start date")
        else:
            years = (end - start).days / 365.25
            if years > cls.MAX_POLICY_DURATION_YEARS:
                flags.append(f"Long policy duration: {years:.1f} years")
        return flags


# ------------------------ Consistency Rules ------------------------

class ConsistencyRules:
    """Data consistency validation"""

    @staticmethod
    def validate_age_dob_consistency(age: int, dob: date) -> List[str]:
        today = date.today()
        calculated = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if abs(calculated - age) > 1:
            return [f"Age mismatch: stated {age}, calculated {calculated}"]
        return []

    @staticmethod
    def validate_date_sequence(start: date, end: date, labels: tuple) -> List[str]:
        if end <= start:
            return [f"{labels[1]} must be after {labels[0]}"]
        return []


# ------------------------ Global Instances ------------------------

field_validation_rules = FieldValidationRules()
business_rules = BusinessRules()
consistency_rules = ConsistencyRules()
