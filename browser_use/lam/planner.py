import json
import os
from typing import Any

from browser_use.llm import ChatGroq, ChatOllama, ChatOpenAI
from browser_use.llm.messages import SystemMessage, UserMessage


class CognitivePlanner:
	"""
	Generates a high-level plan (sequence of steps) to achieve a user goal.
	"""

	def __init__(self, model_name: str = 'gpt-4o'):
		self.model_name = model_name
		self.llm = self._get_llm(model_name)

	def _get_llm(self, model_name: str):
		# ... (Logic to select LLM based on prefix, similar to Summarizer)
		if model_name.startswith('ollama/'):
			return ChatOllama(model=model_name.replace('ollama/', ''))

		if model_name.startswith('groq/'):
			import os

			api_key = os.getenv('GROQ_API_KEY')
			return ChatGroq(model=model_name.replace('groq/', ''), api_key=api_key)

		if model_name.startswith('openrouter/'):
			import os

			api_key = os.getenv('OPENROUTER_API_KEY')
			return ChatOpenAI(
				model=model_name.replace('openrouter/', ''), api_key=api_key, base_url='https://openrouter.ai/api/v1'
			)

		# Normal OpenAI or other providers using OpenAI protocol
		return ChatOpenAI(model=model_name)

	async def plan_task(self, user_request: str) -> list[dict[str, Any]]:
		"""
		Generates a plan (list of steps) for the given user request.
		"""
		system_prompt = """
        You are an expert browser automation planner. Your job is to break down a high-level user request
        into a sequence of logical, actionable steps that a browser agent can execute.

        Steps should be:
        1. Concise and clear.
        2. Logical in order.
        3. Focused on browser interactions (navigate, click, type, extract).

        Return the plan as a JSON list of objects, where each object has:
        - "step_number": integer
        - "description": string (the action to perform)
        - "action_type": string (navigate, interaction, extraction, etc.)
        """

		messages = [
			SystemMessage(content=system_prompt),
			UserMessage(content=f'User Request: {user_request}\n\nGenerate a plan.'),
		]

		try:
			# Enforce JSON output for the plan
			# This is a simplified example; in prod we might use structured output features
			response = await self.llm.ainvoke(messages)
			content = response.completion

			# Simple heuristic to extract JSON list
			if isinstance(content, str):
				# clean markdown code blocks
				clean_content = content.replace('```json', '').replace('```', '').strip()
				plan = json.loads(clean_content)
				if isinstance(plan, list):
					return plan
			return []
		except Exception as e:
			print(f'Error generating plan: {e}')
			return []
