import json
import os
from typing import Any, Dict, List

from browser_use.llm import ChatGroq, ChatOllama, ChatOpenAI
from browser_use.llm.messages import UserMessage, SystemMessage


class CognitivePlanner:
	"""
	Decomposes a high-level user request into a structured list of actionable steps.
	"""

	def __init__(self, model_name: str = 'gpt-4o'):
		self.model_name = model_name
		self.llm = self._get_llm(model_name)

	def _get_llm(self, model_name: str):
		# Default temperature for planning: slightly creative but constrained
		temp = 0.2

		if model_name.startswith('ollama/'):
			return ChatOllama(model=model_name.replace('ollama/', ''))
		
		if model_name.startswith('groq/'):
			api_key = os.getenv('GROQ_API_KEY')
			if not api_key:
				print('[WARN] GROQ_API_KEY not found in .env')
			return ChatGroq(model=model_name.replace('groq/', ''), api_key=api_key, temperature=temp)

		if model_name.startswith('openrouter/'):
			api_key = os.getenv('OPENROUTER_API_KEY')
			return ChatOpenAI(
				model=model_name.replace('openrouter/', ''),
				api_key=api_key,
				base_url='https://openrouter.ai/api/v1',
				temperature=temp
			)
			
		if model_name.startswith('google/'):
			from langchain_google_genai import ChatGoogleGenerativeAI
			api_key = os.getenv('JULES_API_KEY')
			if not api_key:
				print('[WARN] JULES_API_KEY not found in .env')
			# e.g., google/gemini-1.5-pro
			return ChatGoogleGenerativeAI(
				model=model_name.replace('google/', ''),
				api_key=api_key,
				temperature=temp
			)

		# Normal OpenAI or other providers using OpenAI protocol
		return ChatOpenAI(model=model_name, temperature=temp)

	async def plan_task(self, user_request: str) -> List[Dict[str, Any]]:
		"""
		Generates a plan (list of steps) for the given user request.
		"""
		system_prompt = """
        You are an expert task planner for a web navigation agent. 
        Your goal is to break down a user's request into a series of logical, sequential steps.
        Each step should be a clear instruction for a browser automation agent.

        CRITICAL: Output ONLY a JSON list of objects. No explanations before or after.
        
        Required fields for each step object:
        - "description": A short description of the step (e.g., "Navigate to Doctoralia login page").
        - "action_type": The type of action: "navigate", "click", "fill", "extract", "search".
        - "details": Any specific details needed (e.g., URL, selector hint, text to input).

        Example for "Abra o Google e procure por clima":
        [
            {"description": "Navigate to Google", "action_type": "navigate", "details": {"url": "https://google.com"}},
            {"description": "Search for 'clima'", "action_type": "fill", "details": {"selector": "input[name='q']", "value": "clima"}},
            {"description": "Press Enter", "action_type": "click", "details": {"selector": "input[name='btnK']"}}
        ]
        """

		messages = [SystemMessage(content=system_prompt), UserMessage(content=f'Plan this task: {user_request}')]

		try:
			response = await self.llm.ainvoke(messages)
			content = response.completion
			if not isinstance(content, str):
				content = str(content)

			# Extract JSON from potential markdown blocks
			if '```json' in content:
				content = content.split('```json')[1].split('```')[0].strip()
			elif '```' in content:
				# Be careful with naked backticks
				parts = content.split('```')
				if len(parts) >= 3:
					content = parts[1].strip()
				else:
					content = content.strip()
			
			# Strip any potential leading/trailing garbage
			content = content.strip().lstrip('`').rstrip('`').strip()

			try:
				plan = json.loads(content)
			except json.JSONDecodeError:
				# Try to find something that looks like a JSON list
				import re
				match = re.search(r'\[.*\]', content, re.DOTALL)
				if match:
					plan = json.loads(match.group(0))
				else:
					raise

			if not isinstance(plan, list):
				raise ValueError("Plan must be a list of steps")
				
			return plan
		except Exception as e:
			print(f'[LAM] Error generating plan: {e}. Raw content: {content if "content" in locals() else "N/A"}')
			# Fallback to a simple single-step plan
			return [{'description': user_request, 'action_type': 'general', 'details': {}}]
