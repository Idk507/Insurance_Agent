"""Response Agent - Produces final structured output and flags from processed data."""

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.reasoning import ReasoningTools
from config.settings import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_GPT_DEPLOYMENT
)
from config.client_manager import get_llm_client
from utils.exception_handling import setup_openai_exception_suppression  # Handles OpenAI cleanup issues

response_agent = Agent(
    name="Response Agent",
    model=get_llm_client(),
    tools=[ReasoningTools(add_instructions=True)],
    instructions=[
        "You generate the final structured response for an insurance document processor.",
        "Combine all input: mapped fields, validation results, sanity checks.",
        "Return a comprehensive JSON like:",
        """{
            "final_data": { ...clean mapped fields... },
            "validation_flags": [ ... ],
            "sanity_flags": [ ... ],
            "status": "pass" or "fail"
        }"""
    ],
    description="Generates final JSON output with field values and processing flags.",
    markdown=True,
)
