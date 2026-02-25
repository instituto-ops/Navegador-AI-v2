import asyncio
import operator
from typing import List, Dict, Any, Optional, Literal, TypedDict, Annotated

from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from browser_use import Browser
from browser_use.lam.planner import CognitivePlanner
from browser_use.lam.executor import LogicExecutor
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

    def __init__(self, browser: Browser, model_name: str = "gpt-4o"):
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
        builder.add_node("planner", self.planner_node)
        builder.add_node("executor", self.executor_node)
        builder.add_node("summarizer", self.summarizer_node)

        # Define Edges
        builder.set_entry_point("planner")
        builder.add_edge("planner", "executor")

        # Conditional Logic for Executor Loop
        def should_continue(state: AgentState) -> Literal["executor", "summarizer", "__end__"]:
            plan = state.get("plan", [])
            current_index = state.get("current_step_index", 0)

            if not plan:
                return "__end__"

            if current_index < len(plan):
                return "executor"

            return "summarizer"

        builder.add_conditional_edges(
            "executor",
            should_continue
        )

        builder.add_edge("summarizer", END)

        # Compile with checkpointer
        return builder.compile(checkpointer=self.memory)

    async def planner_node(self, state: AgentState):
        messages = state.get("messages", [])
        if not messages:
            return {"plan": []}

        last_message = messages[-1]
        user_request = last_message.content if isinstance(last_message, BaseMessage) else str(last_message)

        print(f"[LAM] Planning task: {user_request}")
        plan = self.planner.plan_task(user_request)

        return {
            "plan": plan,
            "current_step_index": 0
        }

    async def executor_node(self, state: AgentState):
        plan = state.get("plan", [])
        current_index = state.get("current_step_index", 0)

        # Guard clause
        if not plan or current_index >= len(plan):
             return {}

        step = plan[current_index]
        print(f"[LAM] Executing step {current_index + 1}/{len(plan)}: {step.get('description')}")

        result = await self.executor.execute_step(step)

        return {
            "results": [result],
            "current_step_index": current_index + 1
        }

    async def summarizer_node(self, state: AgentState):
        results = state.get("results", [])
        messages = state.get("messages", [])
        user_query = messages[0].content if messages else "Unknown task"

        print(f"[LAM] Summarizing {len(results)} results...")
        summary = self.summarizer.summarize_results(results, user_query)

        return {"final_output": summary}

    async def run(self, input_message: str):
        """
        Runs the graph with the given input message.
        """
        initial_state = {
            "messages": [HumanMessage(content=input_message)],
            "plan": [],
            "current_step_index": 0,
            "results": [],
            "final_output": None
        }

        # Use a generic thread_id for this session since we don't have multi-user context yet
        config = {"configurable": {"thread_id": "1"}}

        async for event in self.graph.astream(initial_state, config=config):
            yield event
