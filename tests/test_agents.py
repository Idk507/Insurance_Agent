"""
Unit Tests for Insurance Processing Agents

Agents Tested:
- OCR Agent
- Language Detector Agent
- Field Mapper Agent
- Validation Agent
- Sanity Agent
- Response Agent

Testing Framework: pytest
"""

import pytest
import json
from unittest.mock import Mock, patch
from datetime import datetime

from agents.ocr_agent import OCRTool
from agents.language_detector_agent import LanguageDetectionTool
from agents.validation_agent import ValidationTool
from agents.sanity_agent import SanityCheckTool
from agents.response_agent import ResponseFormattingTool


class TestOCRAgent:

    def setup_method(self):
        self.ocr_tool = OCRTool()
        self.sample_pdf_content = b"sample pdf content"

    @patch('agents.ocr_agent.fitz')
    def test_ocr_extraction_success(self, mock_fitz):
        mock_doc = Mock()
        mock_page = Mock()
        mock_page.get_text.return_value = "Sample insurance text"
        mock_doc.load_page.return_value = mock_page
        mock_doc.__len__.return_value = 1
        mock_fitz.open.return_value = mock_doc

        result = self.ocr_tool.run(self.sample_pdf_content)

        assert "Sample insurance text" in result
        assert "--- Page 1 ---" in result
        mock_fitz.open.assert_called_once()
        mock_doc.close.assert_called_once()

    @patch('agents.ocr_agent.fitz')
    def test_ocr_extraction_failure(self, mock_fitz):
        mock_fitz.open.side_effect = Exception("PDF parsing error")
        result = self.ocr_tool.run(self.sample_pdf_content)
        assert "OCR processing failed" in result
        assert "PDF parsing error" in result

    @patch('agents.ocr_agent.fitz')
    def test_ocr_multiple_pages(self, mock_fitz):
        mock_doc = Mock()
        mock_page1 = Mock()
        mock_page1.get_text.return_value = "Page 1 content"
        mock_page2 = Mock()
        mock_page2.get_text.return_value = "Page 2 content"
        mock_doc.load_page.side_effect = [mock_page1, mock_page2]
        mock_doc.__len__.return_value = 2
        mock_fitz.open.return_value = mock_doc

        result = self.ocr_tool.run(self.sample_pdf_content)

        assert "--- Page 1 ---" in result
        assert "--- Page 2 ---" in result
        assert "Page 1 content" in result
        assert "Page 2 content" in result


class TestLanguageDetectorAgent:

    def setup_method(self):
        self.lang_tool = LanguageDetectionTool()

    @patch('agents.language_detector_agent.detect')
    def test_english_detection(self, mock_detect):
        mock_detect.return_value = 'en'
        result = self.lang_tool.run("This is an English insurance document")
        assert result == "english"

    @patch('agents.language_detector_agent.detect')
    def test_malay_detection(self, mock_detect):
        mock_detect.return_value = 'ms'
        result = self.lang_tool.run("Ini adalah dokumen insurans Melayu")
        assert result == "malay"

    @patch('agents.language_detector_agent.detect')
    def test_indonesian_mapped_to_malay(self, mock_detect):
        mock_detect.return_value = 'id'
        result = self.lang_tool.run("Dokumen asuransi Indonesia")
        assert result == "malay"

    def test_empty_text_fallback(self):
        result = self.lang_tool.run("")
        assert result == "english"

    @patch('agents.language_detector_agent.detect')
    def test_detection_failure_fallback(self, mock_detect):
        mock_detect.side_effect = Exception("Detection failed")
        result = self.lang_tool.run("Some text")
        assert result == "english"


class TestValidationAgent:

    def setup_method(self):
        self.validation_tool = ValidationTool()
        self.valid_fields = {
            "policy_number": "POL123456",
            "policy_holder_name": "John Doe",
            "age": 35,
            "date_of_birth": "1988-05-15",
            "premium_amount": 1200.50,
            "coverage_amount": 50000.00,
            "policy_start_date": "2024-01-01",
            "policy_end_date": "2025-01-01"
        }

    def test_valid_fields_validation(self):
        result = json.loads(self.validation_tool.run(json.dumps(self.valid_fields)))
        assert result["validation_errors"] == []
        assert len(result["validation_warnings"]) <= 2
        assert result["validated_fields"] == self.valid_fields

    def test_invalid_date_format(self):
        invalid = self.valid_fields.copy()
        invalid["date_of_birth"] = "15-05-1988"
        result = json.loads(self.validation_tool.run(json.dumps(invalid)))
        assert any("Invalid date format" in err for err in result["validation_errors"])

    def test_invalid_age_range(self):
        invalid = self.valid_fields.copy()
        invalid["age"] = 200
        result = json.loads(self.validation_tool.run(json.dumps(invalid)))
        assert any("Invalid age" in err for err in result["validation_errors"])

    def test_negative_amounts(self):
        invalid = self.valid_fields.copy()
        invalid["premium_amount"] = -100
        invalid["coverage_amount"] = -5000
        result = json.loads(self.validation_tool.run(json.dumps(invalid)))
        assert any("premium_amount" in err for err in result["validation_errors"])
        assert any("coverage_amount" in err for err in result["validation_errors"])

    def test_missing_required_fields(self):
        incomplete = {"age": 30}
        result = json.loads(self.validation_tool.run(json.dumps(incomplete)))
        assert any("policy_number" in warn for warn in result["validation_warnings"])


class TestSanityAgent:

    def setup_method(self):
        self.sanity_tool = SanityCheckTool()
        self.validation_data = {
            "validated_fields": {
                "policy_number": "POL123456",
                "policy_holder_name": "John Doe",
                "age": 35,
                "date_of_birth": "1988-05-15",
                "premium_amount": 1200.50,
                "coverage_amount": 50000.00,
                "policy_start_date": "2024-01-01",
                "policy_end_date": "2025-01-01"
            },
            "validation_errors": [],
            "validation_warnings": []
        }

    def test_normal_data_sanity_check(self):
        result = json.loads(self.sanity_tool.run(json.dumps(self.validation_data)))
        assert result["sanity_errors"] == []
        assert len(result["sanity_warnings"]) == 0

    def test_unrealistic_age_check(self):
        test_data = self.validation_data.copy()
        test_data["validated_fields"]["age"] = 150
        result = json.loads(self.sanity_tool.run(json.dumps(test_data)))
        assert any("Unrealistic age" in err for err in result["sanity_errors"])

    def test_minor_age_warning(self):
        test_data = self.validation_data.copy()
        test_data["validated_fields"]["age"] = 16
        result = json.loads(self.sanity_tool.run(json.dumps(test_data)))
        assert any("Minor policy holder" in warn for warn in result["sanity_warnings"])

    def test_high_premium_flag(self):
        test_data = self.validation_data.copy()
        test_data["validated_fields"]["premium_amount"] = 150000
        result = json.loads(self.sanity_tool.run(json.dumps(test_data)))
        assert any("High premium amount" in flag for flag in result["business_flags"])

    def test_coverage_ratio_check(self):
        test_data = self.validation_data.copy()
        test_data["validated_fields"]["coverage_amount"] = 5000
        test_data["validated_fields"]["premium_amount"] = 1000
        result = json.loads(self.sanity_tool.run(json.dumps(test_data)))
        assert any("coverage-to-premium ratio" in warn for warn in result["sanity_warnings"])

    def test_age_dob_consistency(self):
        test_data = self.validation_data.copy()
        test_data["validated_fields"]["age"] = 25
        result = json.loads(self.sanity_tool.run(json.dumps(test_data)))
        assert any("Age mismatch" in err for err in result["sanity_errors"])


class TestResponseAgent:

    def setup_method(self):
        self.response_tool = ResponseFormattingTool()
        self.sanity_data = {
            "sanity_checked_fields": {
                "policy_number": "POL123456",
                "policy_holder_name": "John Doe",
                "age": 35,
                "premium_amount": 1200.50
            },
            "validation_errors": [],
            "validation_warnings": ["Missing required field: address"],
            "sanity_errors": [],
            "sanity_warnings": [],
            "business_flags": []
        }

    def test_successful_response_formatting(self):
        result = json.loads(self.response_tool.run(json.dumps(self.sanity_data)))
        assert result["processing_status"] == "completed_with_warnings"
        assert "processing_timestamp" in result
        assert "extracted_data" in result
        assert "quality_assessment" in result
        assert "summary" in result

    def test_completeness_calculation(self):
        result = json.loads(self.response_tool.run(json.dumps(self.sanity_data)))
        assert isinstance(result["summary"]["data_completeness"], float)

    def test_confidence_calculation(self):
        result = json.loads(self.response_tool.run(json.dumps(self.sanity_data)))
        assert isinstance(result["summary"]["processing_confidence"], float)

    def test_error_status_determination(self):
        test_data = self.sanity_data.copy()
        test_data["validation_errors"] = ["Invalid date format"]
        result = json.loads(self.response_tool.run(json.dumps(test_data)))
        assert result["processing_status"] == "completed_with_errors"

    def test_response_formatting_failure(self):
        invalid_json = "invalid json data"
        result = json.loads(self.response_tool.run(invalid_json))
        assert result["processing_status"] == "failed"
        assert "error" in result


# Fixtures
@pytest.fixture
def sample_pdf_content():
    return b"sample pdf content for testing"

@pytest.fixture
def sample_insurance_data():
    return {
        "policy_number": "POL123456",
        "policy_holder_name": "John Doe",
        "age": 35,
        "date_of_birth": "1988-05-15",
        "address": "123 Main St, City, State",
        "premium_amount": 1200.50,
        "coverage_amount": 50000.00,
        "policy_start_date": "2024-01-01",
        "policy_end_date": "2025-01-01",
        "beneficiary": "Jane Doe"
    }

@pytest.fixture
def sample_validation_result():
    return {
        "validated_fields": {
            "policy_number": "POL123456",
            "policy_holder_name": "John Doe",
            "age": 35
        },
        "validation_errors": [],
        "validation_warnings": ["Missing required field: address"]
    }
