from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from browser_use.agent.views import AgentHistory, AgentHistoryList

if TYPE_CHECKING:
	from browser_use.agent.views import AgentOutput

logger = logging.getLogger(__name__)


class AgentHistoryManager:
	def __init__(self, agent_id: str, history: AgentHistoryList | None = None):
		self.agent_id = agent_id
		self.history = history or AgentHistoryList(history=[], usage=None)

	def add_history_item(self, history_item: AgentHistory) -> None:
		self.history.add_item(history_item)

	def save_to_file(self, file_path: str | Path, sensitive_data: dict[str, str | dict[str, str]] | None = None) -> None:
		try:
			self.history.save_to_file(file_path, sensitive_data)
		except Exception as e:
			logger.error(f'Failed to save history to file: {e}')
			raise e

	def load_from_file(self, file_path: str | Path, output_model: type[AgentOutput]) -> None:
		self.history = AgentHistoryList.load_from_file(file_path, output_model)

	def get_last_action(self) -> dict | None:
		return self.history.last_action()

	def get_errors(self) -> list[str | None]:
		return self.history.errors()

	def get_final_result(self) -> str | None:
		return self.history.final_result()

	def is_done(self) -> bool:
		return self.history.is_done()

	def is_successful(self) -> bool | None:
		return self.history.is_successful()
