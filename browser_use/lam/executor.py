from typing import Any, cast
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_core.language_models.chat_models import BaseChatModel
from browser_use import Agent, Browser
import json

class LogicExecutor:
    """
    Executes browser actions using a specific configuration.
    Wraps browser_use.Agent with specific model settings.
    """

    def __init__(self, browser: Browser, model_name: str = "gpt-4o"):
        self.browser = browser
        self.model_name = model_name
        self.llm = self._get_llm(model_name)

    def _get_llm(self, model_name: str) -> BaseChatModel:
        if model_name.startswith("ollama/"):
            # Ensure we strip 'ollama/' prefix correctly for the model name if needed
            # For ollama lib, model name is usually just 'llama3.2'
            return cast(BaseChatModel, ChatOllama(model=model_name.replace("ollama/", "")))
        return cast(BaseChatModel, ChatOpenAI(model=model_name))

    async def execute_step(self, step: dict[str, Any]) -> dict[str, Any]:
        """
        Executes a single step using the configured browser and LLM.
        """
        task_description = f"Perform action: {step.get('description', '')}. Details: {json.dumps(step.get('details', {}))}"

        try:
            # Cast self.llm to Any to avoid pyright complaining about BaseChatModel protocol mismatch
            # The actual runtime object (ChatOpenAI or ChatOllama) is compatible with what Agent expects
            agent = Agent(
                task=task_description,
                llm=cast(Any, self.llm),
                browser=self.browser,
                use_vision=True
            )

            history = await agent.run()

            # Extract result from history if available
            result = "Completed"
            if history and history.history:
                last_item = history.history[-1]
                if last_item.result and last_item.result[-1].extracted_content:
                    result = last_item.result[-1].extracted_content

            return {
                "step": step,
                "outcome": "Success",
                "result": result,
                "history": history
            }
        except Exception as e:
            return {
                "step": step,
                "outcome": "Failed",
                "error": str(e)
            }
