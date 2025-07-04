"""
Insurance Form Data Models

Defines data models for insurance form processing:
- InsuranceForm: Main structure for insurance policy information
- ProcessingResult: Results from the processing pipeline
- ValidationResult: Validation outcome structure
- QualityAssessment: Metrics for form quality

Technology: Pydantic for data validation and serialization
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class ProcessingStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    COMPLETED_WITH_ERRORS = "completed_with_errors"
    FAILED = "failed"


class LanguageType(str, Enum):
    ENGLISH = "english"
    MALAY = "malay"


class InsuranceForm(BaseModel):
    policy_number: Optional[str]
    policy_holder_name: Optional[str]
    age: Optional[int] = Field(None, ge=0, le=150)
    date_of_birth: Optional[date]
    address: Optional[str]
    beneficiary: Optional[str]
    premium_amount: Optional[float] = Field(None, ge=0)
    coverage_amount: Optional[float] = Field(None, ge=0)
    policy_start_date: Optional[date]
    policy_end_date: Optional[date]
    detected_language: Optional[LanguageType]
    extraction_confidence: Optional[float] = Field(None, ge=0, le=1)

    class Config:
        use_enum_values = True
        json_encoders = {
            date: lambda v: v.isoformat() if v else None,
            datetime: lambda v: v.isoformat() if v else None
        }

    @validator('policy_end_date')
    def validate_policy_dates(cls, v, values):
        if v and values.get('policy_start_date') and v <= values['policy_start_date']:
            raise ValueError('Policy end date must be after start date')
        return v

    @validator('age', 'date_of_birth')
    def validate_age_consistency(cls, v, values, field):
        if field.name == 'date_of_birth' and v and values.get('age'):
            today = date.today()
            calculated_age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
            if abs(calculated_age - values['age']) > 1:
                raise ValueError(f'Age inconsistency: stated {values["age"]}, calculated {calculated_age}')
        return v

    def to_display_dict(self) -> Dict[str, str]:
        return {
            "Policy Number": self.policy_number or "N/A",
            "Policy Holder Name": self.policy_holder_name or "N/A",
            "Age": str(self.age) if self.age is not None else "N/A",
            "Date of Birth": self.date_of_birth.isoformat() if self.date_of_birth else "N/A",
            "Address": self.address or "N/A",
            "Beneficiary": self.beneficiary or "N/A",
            "Premium Amount": f"${self.premium_amount:,.2f}" if self.premium_amount else "N/A",
            "Coverage Amount": f"${self.coverage_amount:,.2f}" if self.coverage_amount else "N/A",
            "Policy Start Date": self.policy_start_date.isoformat() if self.policy_start_date else "N/A",
            "Policy End Date": self.policy_end_date.isoformat() if self.policy_end_date else "N/A",
            "Detected Language": self.detected_language or "N/A"
        }

    def calculate_completeness(self) -> float:
        total_fields = 10
        filled = sum([
            bool(self.policy_number), bool(self.policy_holder_name), bool(self.age),
            bool(self.date_of_birth), bool(self.address), bool(self.beneficiary),
            bool(self.premium_amount), bool(self.coverage_amount),
            bool(self.policy_start_date), bool(self.policy_end_date)
        ])
        return round((filled / total_fields) * 100, 1)


class ValidationError(BaseModel):
    field: str
    message: str
    severity: str = "error"


class ValidationResult(BaseModel):
    is_valid: bool
    errors: List[ValidationError] = []
    warnings: List[ValidationError] = []
    validated_data: Optional[InsuranceForm]

    @property
    def error_count(self) -> int:
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        return len(self.warnings)

    def get_errors_by_field(self, field_name: str) -> List[ValidationError]:
        return [e for e in self.errors if e.field == field_name]


class QualityMetrics(BaseModel):
    data_completeness: float = Field(..., ge=0, le=100)
    processing_confidence: float = Field(..., ge=0, le=100)
    total_errors: int = 0
    total_warnings: int = 0
    business_flags_count: int = 0

    @property
    def quality_score(self) -> float:
        base_score = (self.data_completeness + self.processing_confidence) / 2
        penalty = (self.total_errors * 10) + (self.total_warnings * 5)
        return max(0, min(100, base_score - penalty))

    @property
    def quality_grade(self) -> str:
        score = self.quality_score
        if score >= 90: return "Excellent"
        elif score >= 80: return "Good"
        elif score >= 70: return "Fair"
        elif score >= 60: return "Poor"
        return "Critical"


class ProcessingStep(BaseModel):
    step_name: str
    status: ProcessingStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    output: Optional[Any] = None
    error_message: Optional[str] = None

    @property
    def duration_seconds(self) -> Optional[float]:
        return (self.end_time - self.start_time).total_seconds() if self.end_time else None


class ProcessingResult(BaseModel):
    processing_id: str
    processing_status: ProcessingStatus
    processing_timestamp: datetime = Field(default_factory=datetime.now)
    extracted_data: Optional[InsuranceForm]
    validation_result: Optional[ValidationResult]
    quality_metrics: Optional[QualityMetrics]
    processing_steps: List[ProcessingStep] = []
    validation_errors: List[str] = []
    validation_warnings: List[str] = []
    sanity_errors: List[str] = []
    sanity_warnings: List[str] = []
    business_flags: List[str] = []

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

    def add_processing_step(self, step: ProcessingStep):
        self.processing_steps.append(step)

    def get_step_by_name(self, step_name: str) -> Optional[ProcessingStep]:
        return next((s for s in self.processing_steps if s.step_name == step_name), None)

    @property
    def total_processing_time(self) -> Optional[float]:
        completed_steps = [s for s in self.processing_steps if s.end_time]
        if not completed_steps:
            return None
        start = min(s.start_time for s in completed_steps)
        end = max(s.end_time for s in completed_steps)
        return (end - start).total_seconds()

    def to_summary_dict(self) -> Dict[str, Any]:
        return {
            "Processing ID": self.processing_id,
            "Status": self.processing_status.replace("_", " ").title(),
            "Timestamp": self.processing_timestamp.isoformat(),
            "Total Steps": len(self.processing_steps),
            "Processing Time": f"{self.total_processing_time:.2f}s" if self.total_processing_time else "N/A",
            "Data Completeness": f"{self.quality_metrics.data_completeness}%" if self.quality_metrics else "N/A",
            "Quality Score": f"{self.quality_metrics.quality_score:.1f}" if self.quality_metrics else "N/A",
            "Quality Grade": self.quality_metrics.quality_grade if self.quality_metrics else "N/A"
        }
