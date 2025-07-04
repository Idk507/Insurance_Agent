"""Language Detector Agent - Detects if extracted text is English or Malay."""

from langdetect import detect
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

class LanguageDetectionTool:
    name = "language_detection"
    description = "Detects whether text is in English or Malay."

    def run(self, text: str) -> str:
        logger.info("Running language detection")
        try:
            code = detect(text.strip().replace('\n', ' '))
            lang_map = {'en': 'english', 'ms': 'malay', 'id': 'malay'}
            return lang_map.get(code, 'english')
        except Exception as e:
            logger.error(f"Detection error: {e}")
            return "english"


language_detector_agent = Agent(
    name="Language Detector Agent",
    model=get_llm_client(),
    tools=[ReasoningTools(add_instructions=True), LanguageDetectionTool()],
    instructions=[
        "Use the language_detection tool to identify the primary language.",
        "Return only 'english' or 'malay'. Default to 'english' if unclear.",
    ],
    description="Identifies document language as English or Malay",
    markdown=True,
)
