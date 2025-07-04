"""Sanity Agent - Performs logical checks on validated insurance data."""

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


sanity_agent = Agent(
    name="Sanity Agent",
    model=get_llm_client(),
    tools=[ReasoningTools(add_instructions=True)],
    instructions=[
        "You are a logical reasoning engine that ensures insurance data makes sense.",
        "Check for issues like age > 120, negative premiums, or inconsistent dates.",
        "Return a JSON with: { 'is_sane': true/false, 'issues': [list of logical errors] }",
        "Respond only with the JSON object."
    ],
    description="Checks logical consistency of validated insurance data.",
    markdown=True,
)
