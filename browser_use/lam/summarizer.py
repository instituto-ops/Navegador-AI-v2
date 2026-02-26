from typing import Any, Dict, List

from browser_use.llm import ChatGroq, ChatOllama, ChatOpenAI
from browser_use.llm.messages import SystemMessage, UserMessage


class SemanticSummarizer:
	"""
	Synthesizes execution results into a concise summary.
	"""

	def __init__(self, model_name: str = 'gpt-4o'):
		self.model_name = model_name
		self.llm = self._get_llm(model_name)

	def _get_llm(self, model_name: str):
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
				model=model_name.replace('openrouter/', ''),
				api_key=api_key,
				base_url='https://openrouter.ai/api/v1'
			)

		return ChatOpenAI(model=model_name)

	async def summarize_results(self, results: List[Dict[str, Any]], user_query: str) -> str:
		"""
		Summarizes the execution results in the context of the user query.
		"""
		system_prompt = """
        You are an expert synthesizer. Your task is to take the results of a series of browser automation steps
        and distill them into a clear, actionable summary for the user.

        Focus on the outcome of the request.
        If data was extracted, present it concisely (e.g., as a list or table description).
        If an action was performed, confirm success or failure and any key details.

        Be concise and direct.
        """

		results_text = '\n'.join(
			[
				f'- Step {i + 1}: {step.get("description", "")} -> {step.get("outcome", "Success")}'
				for i, step in enumerate(results)
			]
		)

		messages = [
			SystemMessage(content=system_prompt),
			UserMessage(content=f'User Query: {user_query}\n\nExecution Results:\n{results_text}'),
		]

		try:
			response = await self.llm.ainvoke(messages)
			content = response.completion
			if isinstance(content, str):
				return content
			return str(content)
		except Exception as e:
			print(f'Error generating summary: {e}')
			return 'Task completed.'
