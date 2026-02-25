import json
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI


class CognitivePlanner:
    """
    Decomposes a high-level user request into a structured list of actionable steps.
    """

    def __init__(self, model_name: str = "gpt-4o"):
        self.model_name = model_name
        self.llm = self._get_llm(model_name)

    def _get_llm(self, model_name: str):
        # In a real scenario, this would select between different providers based on config
        # For now, we default to ChatOpenAI (which can point to a local proxy or real API)
        # or ChatOllama if specified.
        if model_name.startswith("ollama/"):
            return ChatOllama(model=model_name.replace("ollama/", ""))
        return ChatOpenAI(model=model_name)

    def plan_task(self, user_request: str) -> List[Dict[str, Any]]:
        """
        Generates a plan (list of steps) for the given user request.
        """
        system_prompt = """
        You are an expert task planner for a web navigation agent.
        Your goal is to break down a user's request into a series of logical, sequential steps.
        Each step should be a clear instruction for a browser automation agent.

        Output a JSON list of objects, where each object has:
        - "description": A short description of the step (e.g., "Navigate to Doctoralia login page").
        - "action_type": The type of action (e.g., "navigate", "click", "fill", "extract").
        - "details": Any specific details needed (e.g., URL, selector hint, text to input).

        Example:
        [
            {"description": "Go to Google", "action_type": "navigate", "details": {"url": "https://google.com"}},
            {"description": "Search for 'weather'", "action_type": "fill", "details": {"selector": "input[name='q']", "value": "weather"}}
        ]
        """

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Plan this task: {user_request}")
        ]

        try:
            response = self.llm.invoke(messages)
            content = response.content
            if not isinstance(content, str):
                 content = str(content)

            # Extract JSON from potential markdown blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            plan = json.loads(content)
            return plan
        except Exception as e:
            print(f"Error generating plan: {e}")
            # Fallback to a simple single-step plan
            return [{"description": user_request, "action_type": "general", "details": {}}]
