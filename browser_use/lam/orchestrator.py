import operator
from typing import Annotated, Any, Dict, List, Literal, Optional, TypedDict, cast

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from browser_use import Browser
from browser_use.lam.executor import LogicExecutor
from browser_use.lam.planner import CognitivePlanner
from browser_use.lam.summarizer import SemanticSummarizer
from browser_use.lam.intelligence import AgentStatus, HumanFeedback, NeuroInsights
from browser_use.llm.messages import BaseMessage, SystemMessage, UserMessage


class AgentState(TypedDict):
	messages: Annotated[List[BaseMessage], operator.add]
	plan: Optional[List[Dict[str, Any]]]
	current_step_index: int
	results: Annotated[List[Dict[str, Any]], operator.add]
	status: AgentStatus
	neuro_insights: Optional[NeuroInsights]
	human_feedback: Optional[HumanFeedback]


class LAMOrchestrator:
	"""
	Orchestrates the cognitive flow using LangGraph.
	Planner -> Loop(Executor) -> Summarizer
	"""

	def __init__(self, browser: Browser, model_name: str = 'gpt-4o'):
		self.browser = browser
		self.model_name = model_name
		self.planner = CognitivePlanner(model_name)
		self.executor = LogicExecutor(browser, model_name)
		self.summarizer = SemanticSummarizer(model_name)
		self.graph = self._build_graph()

	def _build_graph(self):
		workflow = StateGraph(AgentState)

		# Nodes
		workflow.add_node('planner', self.planner_node)
		workflow.add_node('human_approval_gate', self.human_approval_gate_node)
		workflow.add_node('executor', self.executor_node)
		workflow.add_node('summarizer', self.summarizer_node)

		# Edges
		workflow.set_entry_point('planner')
		workflow.add_edge('planner', 'human_approval_gate')

		# Conditional Logic for Executor Loop
		def should_execute(state: AgentState) -> Literal['executor', '__end__']:
			feedback = state.get('human_feedback')
			if feedback and not feedback.get('approved'):
				return '__end__'
			return 'executor'

		workflow.add_conditional_edges('human_approval_gate', should_execute)

		def should_continue(state: AgentState) -> Literal['human_approval_gate', 'summarizer', '__end__']:
			raw_index = state.get('current_step_index', 0)
			current_index = int(cast(Any, raw_index)) if raw_index is not None else 0
			
			plan_list = state.get('plan')
			if plan_list is None:
				plan_list = []

			if not plan_list:
				return '__end__'

			if current_index < len(plan_list):
				return 'human_approval_gate'
			else:
				return 'summarizer'

		workflow.add_conditional_edges('executor', should_continue)
		workflow.add_edge('summarizer', END)

		return workflow.compile(
			checkpointer=MemorySaver(),
			interrupt_before=['human_approval_gate']
		)

	async def planner_node(self, state: AgentState):
		user_request = ''
		messages = state.get('messages', [])
		if messages:
			last_msg = messages[-1]
			if hasattr(last_msg, 'content'):
				user_request = str(last_msg.content)

		print(f'[LAM] Planning task: {user_request}')
		plan_result = await self.planner.plan_task(user_request)
		return {
			'plan': plan_result,
			'current_step_index': state.get('current_step_index', 0),
			'status': 'WAITING_APPROVAL'
		}

	async def human_approval_gate_node(self, state: AgentState):
		print('[LAM] Human Approval Gate Reached. Waiting for feedback...')
		# Default behavior just ensures state captures that it is no longer waiting
		return {'status': 'EXECUTING'}

	async def executor_node(self, state: AgentState):
		plan_val = state.get('plan')
		plan = cast(List[Dict[str, Any]], plan_val) if plan_val is not None else []
		
		raw_index = state.get('current_step_index', 0)
		current_index = int(cast(Any, raw_index)) if raw_index is not None else 0

		# Guard clause
		if not plan or current_index >= len(plan):
			return {}

		step = plan[current_index]
		print(f'[LAM] Executing step {current_index + 1}/{len(plan)}: {step.get("description")}')

		result = await self.executor.execute_step(step)

		return {
			'results': [result],
			'current_step_index': current_index + 1,
		}

	async def summarizer_node(self, state: AgentState):
		user_request = ''
		messages = state.get('messages', [])
		if messages:
			last_msg = messages[-1]
			if hasattr(last_msg, 'content'):
				user_request = str(last_msg.content)

		results_val = state.get('results')
		results = cast(List[Dict[str, Any]], results_val) if results_val is not None else []
		
		print(f'[LAM] Summarizing {len(results)} results')
		summary = await self.summarizer.summarize_results(results, user_request)
		return {'final_output': summary}

	async def run(self, command: str):
		"""
		Async generator that runs the LAM graph and yields events.
		"""
		config: RunnableConfig = {'configurable': {'thread_id': 'lam_session'}}
		initial_state: AgentState = {
			'messages': [UserMessage(content=command)],
			'plan': [],
			'current_step_index': 0,
			'results': [],
			'status': 'PLANNING',
			'neuro_insights': None,
			'human_feedback': None,
		}

		async for event in self.graph.astream(initial_state, config=config):
			yield event
