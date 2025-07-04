"""Field Mapper Agent - Maps extracted text to structured insurance fields."""

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

field_mapper_agent = Agent(
    name="Field Mapper Agent",
    model=get_llm_client(),
    tools=[ReasoningTools(add_instructions=True)],
    instructions=[
        "You are an expert insurance form processor that maps unstructured text to structured fields",
        "Extract and map insurance fields from document text based on the detected language",
        "Use reasoning to understand different form layouts and field variations",
        "Return ONLY a JSON object with these exact fields (use null if not found):",
        """
        {
            "policy_number": "string",
            "policy_holder_name": "string",
            "age": "number",
            "date_of_birth": "YYYY-MM-DD",
            "address": "string",
            "premium_amount": "number",
            "coverage_amount": "number",
            "policy_start_date": "YYYY-MM-DD",
            "policy_end_date": "YYYY-MM-DD",
            "beneficiary": "string"
        }
        """,
        "Be precise with date formats (YYYY-MM-DD) and numeric values",
        "Handle both English and Malay insurance documents",
        "Use reasoning to infer missing information from context when possible",
        "If a field cannot be found or determined, use null as the value"
    ],
    description="Maps unstructured insurance text to structured data fields using AI",
    markdown=True
)
