import asyncio
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
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
        # We could maintain a persistent agent here if browser-use supports it,
        # but for now we re-instantiate with shared browser to keep session alive.
        # To truly persist reasoning context, we'd need to pass history.

    def _get_llm(self, model_name: str):
        if model_name.startswith("ollama/"):
            # Ensure we strip 'ollama/' prefix correctly for the model name if needed
            # For ollama lib, model name is usually just 'llama3.2'
            return ChatOllama(model=model_name.replace("ollama/", ""))
        return ChatOpenAI(model=model_name)

    async def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a single step using the configured browser and LLM.
        """
        task_description = f"Perform action: {step.get('description', '')}. Details: {json.dumps(step.get('details', {}))}"

        # Determine if we should switch model for this specific step type
        # E.g. simple navigation -> use faster model?
        # For now, stick to initialized LLM.

        try:
            agent = Agent(
                task=task_description,
                llm=self.llm,
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
