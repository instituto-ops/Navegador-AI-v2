import json
import os
from typing import Any, cast

from browser_use import Agent, Browser
from browser_use.llm import ChatGroq, ChatOllama, ChatOpenAI


class LogicExecutor:
	"""
	Executes browser actions using a specific configuration.
	Wraps browser_use.Agent with specific model settings.
	"""

	def __init__(self, browser: Browser, model_name: str = 'gpt-4o'):
		self.browser = browser
		self.model_name = model_name
		self.llm = self._get_llm(model_name)

	def _get_llm(self, model_name: str) -> Any:
		if model_name.startswith('ollama/'):
			return ChatOllama(model=model_name.replace('ollama/', ''))
		
		if model_name.startswith('groq/'):
			api_key = os.getenv('GROQ_API_KEY')
			return ChatGroq(model=model_name.replace('groq/', ''), api_key=api_key)

		if model_name.startswith('openrouter/'):
			api_key = os.getenv('OPENROUTER_API_KEY')
			return ChatOpenAI(
				model=model_name.replace('openrouter/', ''),
				api_key=api_key,
				base_url='https://openrouter.ai/api/v1'
			)

		return ChatOpenAI(model=model_name)

	async def execute_step(self, step: dict[str, Any]) -> dict[str, Any]:
		"""
		Executes a single step using the configured browser and LLM.
		"""
		task_description = f'Perform action: {step.get("description", "")}. Details: {json.dumps(step.get("details", {}))}'

		try:
			# Disable vision for Groq as it doesn't support image inputs (causes 400 error)
			use_vision = not self.model_name.startswith('groq/')
			
			agent = Agent(
				task=task_description, 
				llm=cast(Any, self.llm), 
				browser=self.browser, 
				use_vision=use_vision
			)

			history = await agent.run()

			# Extract result from history if available
			result = 'Completed'
			if history and history.history:
				last_item = history.history[-1]
				if last_item.result and last_item.result:
					# Find the last non-empty result
					for r in reversed(last_item.result):
						if r.extracted_content:
							result = r.extracted_content
							break

			return {'step': step, 'outcome': 'Success', 'result': result, 'history': history}
		except Exception as e:
			print(f'[LAM] Error executing step: {e}')
			return {'step': step, 'outcome': 'Failed', 'error': str(e)}
