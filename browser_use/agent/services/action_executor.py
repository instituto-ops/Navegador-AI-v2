from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from browser_use.agent.views import ActionResult, AgentHistory
from browser_use.dom.views import DOMInteractedElement, MatchLevel
from browser_use.llm.base import BaseChatModel
from browser_use.llm.messages import SystemMessage, UserMessage
from browser_use.utils import sanitize_surrogates

if TYPE_CHECKING:
	from browser_use.browser.session import BrowserSession
	from browser_use.browser.views import BrowserStateSummary
	from browser_use.filesystem.file_system import FileSystem
	from browser_use.tools.registry.views import ActionModel
	from browser_use.tools.service import Tools

logger = logging.getLogger(__name__)


class AgentActionExecutor:
	def __init__(
		self,
		browser_session: BrowserSession,
		tools: Tools,
		file_system: FileSystem,
		logger: logging.Logger,
		action_submitting_llm: BaseChatModel,
		page_extraction_llm: BaseChatModel | None,
		extraction_schema: dict | None,
		sensitive_data: dict[str, str | dict[str, str]] | None,
		available_file_paths: list[str] | None,
		check_stop_or_pause_callback: Callable[[], Any] | None = None,
		demo_mode_log_callback: Callable[[str, str, dict[str, Any] | None], Any] | None = None,
	):
		self.browser_session = browser_session
		self.tools = tools
		self.file_system = file_system
		self.logger = logger
		self.action_submitting_llm = action_submitting_llm
		self.page_extraction_llm = page_extraction_llm
		self.extraction_schema = extraction_schema
		self.sensitive_data = sensitive_data
		self.available_file_paths = available_file_paths or []
		self.check_stop_or_pause_callback = check_stop_or_pause_callback
		self.demo_mode_log_callback = demo_mode_log_callback

	@property
	def browser_profile(self):
		return self.browser_session.browser_profile

	async def execute_actions(self, actions: list[ActionModel], current_step_number: int) -> list[ActionResult]:
		"""Execute multiple actions with page-change guards."""
		results: list[ActionResult] = []
		total_actions = len(actions)

		assert self.browser_session is not None, 'BrowserSession is not set up'

		for i, action in enumerate(actions):
			action_data = action.model_dump(exclude_unset=True)
			action_name = next(iter(action_data.keys())) if action_data else 'unknown'

			if i > 0:
				if action_data.get('done') is not None:
					msg = f'Done action is allowed only as a single action - stopped after action {i} / {total_actions}.'
					self.logger.debug(msg)
					break

			if i > 0:
				self.logger.debug(f'Waiting {self.browser_profile.wait_between_actions} seconds between actions')
				await asyncio.sleep(self.browser_profile.wait_between_actions)

			try:
				if self.check_stop_or_pause_callback:
					await self.check_stop_or_pause_callback()

				await self._log_action(action, action_name, i + 1, total_actions, current_step_number)

				pre_action_url = await self.browser_session.get_current_page_url()
				pre_action_focus = self.browser_session.agent_focus_target_id

				result = await self.tools.act(
					action=action,
					browser_session=self.browser_session,
					file_system=self.file_system,
					page_extraction_llm=self.page_extraction_llm,
					sensitive_data=self.sensitive_data,
					available_file_paths=self.available_file_paths,
					extraction_schema=self.extraction_schema,
				)

				if result.error:
					await self._demo_mode_log(
						f'Action "{action_name}" failed: {result.error}',
						'error',
						{'action': action_name, 'step': current_step_number},
					)
				elif result.is_done:
					completion_text = result.long_term_memory or result.extracted_content or 'Task marked as done.'
					level = 'success' if result.success is not False else 'warning'
					await self._demo_mode_log(
						completion_text,
						level,
						{'action': action_name, 'step': current_step_number},
					)

				results.append(result)

				if results[-1].is_done or results[-1].error or i == total_actions - 1:
					break

				registered_action = self.tools.registry.registry.actions.get(action_name)
				if registered_action and registered_action.terminates_sequence:
					self.logger.info(
						f'Action "{action_name}" terminates sequence — skipping {total_actions - i - 1} remaining action(s)'
					)
					break

				post_action_url = await self.browser_session.get_current_page_url()
				post_action_focus = self.browser_session.agent_focus_target_id

				if post_action_url != pre_action_url or post_action_focus != pre_action_focus:
					self.logger.info(f'Page changed after "{action_name}" — skipping {total_actions - i - 1} remaining action(s)')
					break

			except Exception as e:
				self.logger.error(f'❌ Executing action {i + 1} failed -> {type(e).__name__}: {e}')
				await self._demo_mode_log(
					f'Action "{action_name}" raised {type(e).__name__}: {e}',
					'error',
					{'action': action_name, 'step': current_step_number},
				)
				raise e

		return results

	async def _log_action(self, action, action_name: str, action_num: int, total_actions: int, current_step_number: int) -> None:
		blue = '\033[34m'
		magenta = '\033[35m'
		reset = '\033[0m'

		if total_actions > 1:
			action_header = f'▶️  [{action_num}/{total_actions}] {blue}{action_name}{reset}:'
			plain_header = f'▶️  [{action_num}/{total_actions}] {action_name}:'
		else:
			action_header = f'▶️   {blue}{action_name}{reset}:'
			plain_header = f'▶️  {action_name}:'

		action_data = action.model_dump(exclude_unset=True)
		params = action_data.get(action_name, {})

		param_parts = []
		plain_param_parts = []

		if params and isinstance(params, dict):
			for param_name, value in params.items():
				if isinstance(value, str) and len(value) > 150:
					display_value = value[:150] + '...'
				elif isinstance(value, list) and len(str(value)) > 200:
					display_value = str(value)[:200] + '...'
				else:
					display_value = value

				param_parts.append(f'{magenta}{param_name}{reset}: {display_value}')
				plain_param_parts.append(f'{param_name}: {display_value}')

		if param_parts:
			params_string = ', '.join(param_parts)
			self.logger.info(f'  {action_header} {params_string}')
		else:
			self.logger.info(f'  {action_header}')

		panel_message = plain_header
		if plain_param_parts:
			panel_message = f'{panel_message} {", ".join(plain_param_parts)}'
		await self._demo_mode_log(panel_message.strip(), 'action', {'action': action_name, 'step': current_step_number})

	async def _demo_mode_log(self, message: str, level: str = 'info', metadata: dict[str, Any] | None = None) -> None:
		if self.demo_mode_log_callback:
			await self.demo_mode_log_callback(message, level, metadata)

	async def execute_ai_step(
		self,
		query: str,
		llm: BaseChatModel,
		include_screenshot: bool = False,
		extract_links: bool = False,
	) -> ActionResult:
		"""Execute an AI step during rerun to re-evaluate extract actions."""
		from browser_use.agent.prompts import get_ai_step_system_prompt, get_ai_step_user_prompt, get_rerun_summary_message
		from browser_use.dom.markdown_extractor import extract_clean_markdown

		self.logger.debug(f'Using LLM for AI step: {llm.model}')

		try:
			content, content_stats = await extract_clean_markdown(
				browser_session=self.browser_session, extract_links=extract_links
			)
		except Exception as e:
			return ActionResult(error=f'Could not extract clean markdown: {type(e).__name__}: {e}')

		screenshot_b64 = None
		if include_screenshot:
			try:
				screenshot = await self.browser_session.take_screenshot(full_page=False)
				if screenshot:
					import base64

					screenshot_b64 = base64.b64encode(screenshot).decode('utf-8')
			except Exception as e:
				self.logger.warning(f'Failed to capture screenshot for ai_step: {e}')

		original_html_length = content_stats['original_html_chars']
		initial_markdown_length = content_stats['initial_markdown_chars']
		final_filtered_length = content_stats['final_filtered_chars']
		chars_filtered = content_stats['filtered_chars_removed']

		stats_summary = f'Content processed: {original_html_length:,} HTML chars → {initial_markdown_length:,} initial markdown → {final_filtered_length:,} filtered markdown'
		if chars_filtered > 0:
			stats_summary += f' (filtered {chars_filtered:,} chars of noise)'

		content = sanitize_surrogates(content)
		query = sanitize_surrogates(query)

		system_prompt = get_ai_step_system_prompt()
		prompt_text = get_ai_step_user_prompt(query, stats_summary, content)

		if screenshot_b64:
			user_message = get_rerun_summary_message(prompt_text, screenshot_b64)
		else:
			user_message = UserMessage(content=prompt_text)

		try:
			response = await asyncio.wait_for(llm.ainvoke([SystemMessage(content=system_prompt), user_message]), timeout=120.0)

			current_url = await self.browser_session.get_current_page_url()
			extracted_content = (
				f'<url>\n{current_url}\n</url>\n<query>\n{query}\n</query>\n<result>\n{response.completion}\n</result>'
			)

			MAX_MEMORY_LENGTH = 1000
			if len(extracted_content) < MAX_MEMORY_LENGTH:
				memory = extracted_content
				include_extracted_content_only_once = False
			else:
				file_name = await self.file_system.save_extracted_content(extracted_content)
				memory = f'Query: {query}\nContent in {file_name} and once in <read_state>.'
				include_extracted_content_only_once = True

			self.logger.info(f'🤖 AI Step: {memory}')
			return ActionResult(
				extracted_content=extracted_content,
				include_extracted_content_only_once=include_extracted_content_only_once,
				long_term_memory=memory,
			)
		except Exception as e:
			self.logger.warning(f'Failed to execute AI step: {e.__class__.__name__}: {e}')
			self.logger.debug('Full error traceback:', exc_info=True)
			return ActionResult(error=f'AI step failed: {e}')

	async def wait_for_minimum_elements(
		self,
		min_elements: int,
		timeout: float = 30.0,
		poll_interval: float = 1.0,
	) -> BrowserStateSummary | None:
		"""Wait for the page to have at least min_elements interactive elements."""
		assert self.browser_session is not None, 'BrowserSession is not set up'

		start_time = time.time()
		last_count = 0

		while (time.time() - start_time) < timeout:
			state = await self.browser_session.get_browser_state_summary(include_screenshot=False)
			if state and state.dom_state.selector_map:
				current_count = len(state.dom_state.selector_map)
				if current_count >= min_elements:
					self.logger.debug(f'✅ Page has {current_count} elements (needed {min_elements}), proceeding with action')
					return state
				if current_count != last_count:
					self.logger.debug(
						f'⏳ Waiting for elements: {current_count}/{min_elements} '
						f'(timeout in {timeout - (time.time() - start_time):.1f}s)'
					)
					last_count = current_count
			await asyncio.sleep(poll_interval)

		self.logger.warning(f'⚠️ Timeout waiting for {min_elements} elements, proceeding with {last_count} elements')
		return await self.browser_session.get_browser_state_summary(include_screenshot=False)

	async def update_action_indices(
		self,
		historical_element: DOMInteractedElement | None,
		action: ActionModel,
		browser_state_summary: BrowserStateSummary,
	) -> ActionModel | None:
		"""Update action indices based on current page state."""
		if not historical_element or not browser_state_summary.dom_state.selector_map:
			return action

		selector_map = browser_state_summary.dom_state.selector_map
		highlight_index: int | None = None
		match_level: MatchLevel | None = None

		# Level 1: EXACT hash match
		for idx, elem in selector_map.items():
			if elem.element_hash == historical_element.element_hash:
				highlight_index = idx
				match_level = MatchLevel.EXACT
				break

		# Level 2: STABLE hash match
		if highlight_index is None and historical_element.stable_hash is not None:
			for idx, elem in selector_map.items():
				if elem.compute_stable_hash() == historical_element.stable_hash:
					highlight_index = idx
					match_level = MatchLevel.STABLE
					break

		# Level 3: XPATH match
		if highlight_index is None and historical_element.x_path:
			for idx, elem in selector_map.items():
				if elem.xpath == historical_element.x_path:
					highlight_index = idx
					match_level = MatchLevel.XPATH
					break

		# Level 4: AX_NAME match
		if highlight_index is None and historical_element.ax_name:
			hist_name = historical_element.node_name.lower()
			hist_ax_name = historical_element.ax_name
			for idx, elem in selector_map.items():
				elem_ax_name = elem.ax_node.name if elem.ax_node else None
				if elem.node_name.lower() == hist_name and elem_ax_name == hist_ax_name:
					highlight_index = idx
					match_level = MatchLevel.AX_NAME
					break

		# Level 5: ATTRIBUTE match
		if highlight_index is None and historical_element.attributes:
			hist_attrs = historical_element.attributes
			hist_name = historical_element.node_name.lower()
			for attr_key in ['name', 'id', 'aria-label']:
				if attr_key in hist_attrs and hist_attrs[attr_key]:
					for idx, elem in selector_map.items():
						if (
							elem.node_name.lower() == hist_name
							and elem.attributes
							and elem.attributes.get(attr_key) == hist_attrs[attr_key]
						):
							highlight_index = idx
							match_level = MatchLevel.ATTRIBUTE
							break
					if highlight_index is not None:
						break

		if highlight_index is None:
			return None

		old_index = action.get_index()
		if old_index != highlight_index:
			action.set_index(highlight_index)
			level_name = match_level.name if match_level else 'UNKNOWN'
			self.logger.info(f'Element index updated {old_index} → {highlight_index} (matched at {level_name} level)')

		return action

	def format_element_for_error(self, elem: DOMInteractedElement | None) -> str:
		"""Format element info for error messages."""
		if elem is None:
			return '<no element recorded>'

		parts = [f'<{elem.node_name}>']
		if elem.attributes:
			for key in ['name', 'id', 'aria-label', 'type']:
				if key in elem.attributes and elem.attributes[key]:
					parts.append(f'{key}="{elem.attributes[key]}"')

		parts.append(f'hash={elem.element_hash}')
		if elem.stable_hash:
			parts.append(f'stable_hash={elem.stable_hash}')

		if elem.x_path:
			xpath_short = elem.x_path if len(elem.x_path) <= 60 else f'...{elem.x_path[-57:]}'
			parts.append(f'xpath="{xpath_short}"')

		return ' '.join(parts)

	def count_expected_elements_from_history(self, history_item: AgentHistory) -> int:
		"""Estimate the minimum number of elements expected based on history."""
		if not history_item.model_output or not history_item.model_output.action:
			return 0

		max_index = -1
		for action in history_item.model_output.action:
			index = action.get_index()
			if index is not None:
				max_index = max(max_index, index)

		return min(max_index + 1, 50) if max_index >= 0 else 0

	def is_redundant_retry_step(
		self,
		current_item: AgentHistory,
		previous_item: AgentHistory | None,
		previous_step_succeeded: bool,
	) -> bool:
		"""Detect if current step is a redundant retry of the previous step."""
		if not previous_item or not previous_step_succeeded:
			return False

		curr_elements = current_item.state.interacted_element
		prev_elements = previous_item.state.interacted_element

		if not curr_elements or not prev_elements:
			return False

		curr_elem = curr_elements[0] if curr_elements else None
		prev_elem = prev_elements[0] if prev_elements else None

		if not curr_elem or not prev_elem:
			return False

		same_by_hash = curr_elem.element_hash == prev_elem.element_hash
		same_by_stable_hash = (
			curr_elem.stable_hash is not None
			and prev_elem.stable_hash is not None
			and curr_elem.stable_hash == prev_elem.stable_hash
		)
		same_by_xpath = curr_elem.x_path == prev_elem.x_path

		if not (same_by_hash or same_by_stable_hash or same_by_xpath):
			return False

		curr_actions = current_item.model_output.action if current_item.model_output else []
		prev_actions = previous_item.model_output.action if previous_item.model_output else []

		if not curr_actions or not prev_actions:
			return False

		curr_action_data = curr_actions[0].model_dump(exclude_unset=True)
		prev_action_data = prev_actions[0].model_dump(exclude_unset=True)

		curr_action_type = next(iter(curr_action_data.keys()), None)
		prev_action_type = next(iter(prev_action_data.keys()), None)

		if curr_action_type != prev_action_type:
			return False

		self.logger.debug(
			f'🔄 Detected redundant retry: both steps target same element '
			f'<{curr_elem.node_name}> with action "{curr_action_type}"'
		)

		return True

	def is_menu_opener_step(self, history_item: AgentHistory | None) -> bool:
		"""Detect if a step opens a dropdown/menu."""
		if not history_item or not history_item.state or not history_item.state.interacted_element:
			return False

		elem = history_item.state.interacted_element[0] if history_item.state.interacted_element else None
		if not elem:
			return False

		attrs = elem.attributes or {}

		if attrs.get('aria-haspopup') in ('true', 'menu', 'listbox'):
			return True
		if attrs.get('data-gw-click') == 'toggleSubMenu':
			return True
		if 'expand-button' in attrs.get('class', ''):
			return True
		if attrs.get('role') == 'menuitem' and attrs.get('aria-expanded') in ('false', 'true'):
			return True
		if attrs.get('role') == 'button' and attrs.get('aria-expanded') in ('false', 'true'):
			return True

		return False

	def is_menu_item_element(self, elem: DOMInteractedElement | None) -> bool:
		"""Detect if an element is a menu item that appears inside a dropdown/menu."""
		if not elem:
			return False

		attrs = elem.attributes or {}

		role = attrs.get('role', '')
		if role in ('menuitem', 'option', 'menuitemcheckbox', 'menuitemradio', 'treeitem'):
			return True

		if 'gw-action--inner' in attrs.get('class', ''):
			return True
		if 'menuitem' in attrs.get('class', '').lower():
			return True

		if elem.ax_name and elem.ax_name not in ('', None):
			elem_class = attrs.get('class', '').lower()
			if any(x in elem_class for x in ['dropdown', 'popup', 'menu', 'submenu', 'action']):
				return True

		return False

	async def reexecute_menu_opener(
		self,
		opener_item: AgentHistory,
		ai_step_llm: BaseChatModel | None = None,
	) -> bool:
		"""Re-execute a menu opener step to re-open a closed dropdown."""
		try:
			self.logger.info('🔄 Re-opening dropdown/menu by re-executing previous step...')
			await self.execute_history_step(opener_item, delay=0.5, ai_step_llm=ai_step_llm, wait_for_elements=False)
			await asyncio.sleep(0.3)
			return True
		except Exception as e:
			self.logger.warning(f'Failed to re-open dropdown: {e}')
			return False

	async def execute_history_step(
		self,
		history_item: AgentHistory,
		delay: float,
		ai_step_llm: BaseChatModel | None = None,
		wait_for_elements: bool = False,
	) -> list[ActionResult]:
		"""Execute a single step from history with element validation."""
		assert self.browser_session is not None, 'BrowserSession is not set up'

		await asyncio.sleep(delay)

		if wait_for_elements:
			needs_element_matching = False
			if history_item.model_output:
				for i, action in enumerate(history_item.model_output.action):
					action_data = action.model_dump(exclude_unset=True)
					action_name = next(iter(action_data.keys()), None)
					if action_name in ('click', 'input', 'hover', 'select_option', 'drag_and_drop'):
						historical_elem = (
							history_item.state.interacted_element[i] if i < len(history_item.state.interacted_element) else None
						)
						if historical_elem is not None:
							needs_element_matching = True
							break

			if needs_element_matching:
				min_elements = self.count_expected_elements_from_history(history_item)
				if min_elements > 0:
					state = await self.wait_for_minimum_elements(min_elements, timeout=15.0, poll_interval=1.0)
				else:
					state = await self.browser_session.get_browser_state_summary(include_screenshot=False)
			else:
				state = await self.browser_session.get_browser_state_summary(include_screenshot=False)
		else:
			state = await self.browser_session.get_browser_state_summary(include_screenshot=False)
		if not state or not history_item.model_output:
			raise ValueError('Invalid state or model output')

		results = []
		pending_actions = []

		for i, action in enumerate(history_item.model_output.action):
			action_data = action.model_dump(exclude_unset=True)
			action_name = next(iter(action_data.keys()), None)

			if action_name == 'extract':
				if pending_actions:
					batch_results = await self.execute_actions(
						pending_actions, current_step_number=history_item.metadata.step_number if history_item.metadata else 0
					)
					results.extend(batch_results)
					pending_actions = []

				extract_params = action_data['extract']
				query = extract_params.get('query', '')
				extract_links = extract_params.get('extract_links', False)

				self.logger.info(f'🤖 Using AI step for extract action: {query[:50]}...')
				ai_result = await self.execute_ai_step(
					query=query,
					include_screenshot=False,
					extract_links=extract_links,
					llm=ai_step_llm or self.action_submitting_llm,
				)
				results.append(ai_result)
			else:
				historical_elem = history_item.state.interacted_element[i]
				updated_action = await self.update_action_indices(
					historical_elem,
					action,
					state,
				)
				if updated_action is None:
					elem_info = self.format_element_for_error(historical_elem)
					selector_map = state.dom_state.selector_map or {}
					selector_count = len(selector_map)

					hist_node = historical_elem.node_name.lower() if historical_elem else ''
					similar_elements = []
					if historical_elem and historical_elem.attributes:
						hist_aria = historical_elem.attributes.get('aria-label', '')
						for idx, elem in selector_map.items():
							if elem.node_name.lower() == hist_node and elem.attributes:
								elem_aria = elem.attributes.get('aria-label', '')
								if elem_aria:
									similar_elements.append(f'{idx}:{elem_aria[:30]}')
									if len(similar_elements) >= 5:
										break

					diagnostic = ''
					if similar_elements:
						diagnostic = f'\n  Available <{hist_node.upper()}> with aria-label: {similar_elements}'
					elif hist_node:
						same_node_count = sum(1 for e in selector_map.values() if e.node_name.lower() == hist_node)
						diagnostic = (
							f'\n  Found {same_node_count} <{hist_node.upper()}> elements (none with matching identifiers)'
						)

					raise ValueError(
						f'Could not find matching element for action {i} in current page.\n'
						f'  Looking for: {elem_info}\n'
						f'  Page has {selector_count} interactive elements.{diagnostic}\n'
						f'  Tried: EXACT hash → STABLE hash → XPATH → AX_NAME → ATTRIBUTE matching'
					)
				pending_actions.append(updated_action)

		if pending_actions:
			batch_results = await self.execute_actions(
				pending_actions, current_step_number=history_item.metadata.step_number if history_item.metadata else 0
			)
			results.extend(batch_results)

		return results
