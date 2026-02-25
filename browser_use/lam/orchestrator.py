import operator
from typing import Annotated, Any, Dict, List, Literal, Optional, TypedDict, cast

from browser_use.llm.messages import UserMessage, SystemMessage, BaseMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from browser_use import Browser
from browser_use.lam.executor import LogicExecutor
from browser_use.lam.planner import CognitivePlanner
from browser_use.lam.summarizer import SemanticSummarizer


# Define AgentState with Annotated for proper state merging/appending
class AgentState(TypedDict):
	messages: Annotated[List[BaseMessage], operator.add]
	plan: Optional[List[Dict[str, Any]]]
	current_step_index: int
	results: Annotated[List[Dict[str, Any]], operator.add]
	final_output: Optional[str]


class LAMOrchestrator:
	"""
	Orchestrates the LAM workflow using LangGraph.
	Includes persistence via MemorySaver for durable execution.
	"""

	def __init__(self, browser: Browser, model_name: str = 'gpt-4o'):
		self.browser = browser
		self.model_name = model_name
		self.planner = CognitivePlanner(model_name=model_name)
		self.executor = LogicExecutor(browser=browser, model_name=model_name)
		self.summarizer = SemanticSummarizer(model_name=model_name)

		# Initialize Checkpointer for state persistence
		self.memory = MemorySaver()
		self.graph = self._build_graph()

	def _build_graph(self):
		builder = StateGraph(AgentState)

		# Define Nodes
		builder.add_node('planner', self.planner_node)
		builder.add_node('executor', self.executor_node)
		builder.add_node('summarizer', self.summarizer_node)

		# Define Edges
		builder.set_entry_point('planner')
		builder.add_edge('planner', 'executor')

		# Conditional Logic for Executor Loop
		def should_continue(state: AgentState) -> Literal['executor', 'summarizer', '__end__']:
			raw_index = state.get('current_step_index', 0)
			current_index = int(raw_index) if raw_index is not None else 0
			
			plan_list = state.get('plan') or []

			if not plan_list:
				return '__end__'

			if current_index < len(plan_list):
				return 'executor'

			return 'summarizer'

		builder.add_conditional_edges('executor', should_continue)

		builder.add_edge('summarizer', END)

		# Compile with checkpointer
		return builder.compile(checkpointer=self.memory)

	async def planner_node(self, state: AgentState):
		messages = state.get('messages', [])
		if not messages:
			return {'plan': []}

		last_message = messages[-1]
		if hasattr(last_message, 'content'):
			user_request = str(last_message.content)
		else:
			user_request = str(last_message)

		print(f'[LAM] Planning task: {user_request}')
		plan = await self.planner.plan_task(user_request)

		return {'plan': plan, 'current_step_index': 0}

	async def executor_node(self, state: AgentState):
		plan = state.get('plan') or []
		raw_index = state.get('current_step_index', 0)
		current_index = int(raw_index) if raw_index is not None else 0

		# Guard clause
		if not plan or current_index >= len(plan):
			return {}

		step = cast(Dict[str, Any], plan[current_index])
		print(f'[LAM] Executing step {current_index + 1}/{len(plan)}: {step.get("description")}')

		result = await self.executor.execute_step(step)

		return {'results': [result], 'current_step_index': current_index + 1}

	async def summarizer_node(self, state: AgentState):
		results = state.get('results', [])
		messages = state.get('messages', [])
		user_query = 'Unknown task'
		if messages:
			msg = messages[0]
			if hasattr(msg, 'content'):
				user_query = str(msg.content)
			else:
				user_query = str(msg)

		print(f'[LAM] Summarizing {len(results)} results...')
		summary = await self.summarizer.summarize_results(results, user_query)

		return {'final_output': summary}

	async def run(self, input_message: str):
		"""
		Runs the graph with the given input message.
		"""
		initial_state: AgentState = {
			'messages': [UserMessage(content=input_message)],
			'plan': [],
			'current_step_index': 0,
			'results': [],
			'final_output': None,
		}

		# Use a generic thread_id for this session since we don't have multi-user context yet
		config_dict = {'configurable': {'thread_id': '1'}}
		# Cast to RunnableConfig to satisfy type checker
		config = cast(RunnableConfig, config_dict)

		async for event in self.graph.astream(initial_state, config=config):
			yield event
