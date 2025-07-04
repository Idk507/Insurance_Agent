"""Validation Agent - Performs rule-based validation on extracted fields."""

import json
from datetime import datetime
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.reasoning import ReasoningTools
from agno.utils.log import logger
from config.settings import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_GPT_DEPLOYMENT
)

from config.client_manager import get_llm_client
from utils.exception_handling import setup_openai_exception_suppression  # Handles OpenAI cleanup issues

class ValidationTool:
    """Tool for validating insurance field data"""
    name = "field_validation"
    description = "Validates insurance field data using rule-based checks"

    def run(self, mapped_fields_json: str) -> str:
        logger.info("Starting field validation")
        try:
            fields = json.loads(mapped_fields_json) if isinstance(mapped_fields_json, str) else mapped_fields_json

            validation_results = {
                "validated_fields": fields.copy(),
                "validation_errors": [],
                "validation_warnings": []
            }

            # Date validation
            for field in ["date_of_birth", "policy_start_date", "policy_end_date"]:
                if fields.get(field):
                    try:
                        datetime.strptime(fields[field], "%Y-%m-%d")
                    except ValueError:
                        validation_results["validation_errors"].append(
                            f"Invalid date format for {field}: {fields[field]}"
                        )

            # Age
            age = fields.get("age")
            if age is not None and (not isinstance(age, (int, float)) or not (0 <= age <= 150)):
                validation_results["validation_errors"].append(f"Invalid age: {age}. Must be between 0-150")

            # Amounts
            for key in ["premium_amount", "coverage_amount"]:
                amount = fields.get(key)
                if amount is not None and (not isinstance(amount, (int, float)) or amount < 0):
                    validation_results["validation_errors"].append(f"Invalid {key}: {amount}. Must be positive")

            # Required fields
            for field in ["policy_number", "policy_holder_name"]:
                if not fields.get(field):
                    validation_results["validation_warnings"].append(f"Missing required field: {field}")

            logger.info("Validation completed")
            return json.dumps(validation_results, indent=2)

        except Exception as e:
            error_msg = f"Validation failed: {str(e)}"
            logger.error(error_msg)
            return json.dumps({"error": error_msg})

validation_agent = Agent(
    name="Validation Agent",
    model=get_llm_client(),
    tools=[ReasoningTools(add_instructions=True), ValidationTool()],
    instructions=[
        "You are a data validation specialist for insurance forms",
        "Use the field_validation tool to check mapped insurance data for errors",
        "Use reasoning to identify data quality issues and inconsistencies",
        "Validate date formats, numeric ranges, and required fields",
        "Return validation results with errors and warnings clearly identified",
        "Focus on data quality and consistency checks"
    ],
    description="Validates insurance field data using rule-based validation checks",
    markdown=True
)
