import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from browser_use.dom.views import DOMRect, EnhancedDOMTreeNode, NodeType

# Mock necessary modules
from browser_use.mcp.server import BrowserUseServer


@pytest.fixture
def mock_dependencies():
	with (
		patch('browser_use.mcp.server.Server') as mock_server_cls,
		patch('browser_use.mcp.server.BrowserSession') as mock_session_cls,
		patch('browser_use.mcp.server.Agent') as mock_agent_cls,
		patch('browser_use.mcp.server.Tools') as mock_tools_cls,
		patch('browser_use.mcp.server.ChatOpenAI') as mock_llm_cls,
		patch('browser_use.mcp.server.ProductTelemetry') as mock_telemetry_cls,
		patch('browser_use.mcp.server.FileSystem') as mock_fs_cls,
		patch('browser_use.mcp.server.load_browser_use_config') as mock_config,
	):
		mock_config.return_value = {'llm': {'api_key': 'test-key'}}

		# Setup mock session
		mock_session = mock_session_cls.return_value
		mock_session.id = 'test-session-id'
		mock_session.start = AsyncMock()
		mock_session.close = AsyncMock()
		mock_session.kill = AsyncMock()
		mock_session.event_bus = MagicMock()
		mock_session.event_bus.dispatch = AsyncMock()
		mock_session.get_dom_element_by_index = AsyncMock()
		mock_session.get_browser_state_summary = AsyncMock()
		mock_session.get_tabs = AsyncMock()
		mock_session.get_target_id_from_tab_id = AsyncMock()
		mock_session.get_current_page_url = AsyncMock()
		mock_session.current_url = 'https://mock-url.com'

		# Setup mock agent
		mock_agent = mock_agent_cls.return_value
		mock_agent.run = AsyncMock()
		mock_agent.close = AsyncMock()

		yield {
			'server_cls': mock_server_cls,
			'session_cls': mock_session_cls,
			'session': mock_session,
			'agent_cls': mock_agent_cls,
			'agent': mock_agent,
			'tools_cls': mock_tools_cls,
			'llm_cls': mock_llm_cls,
			'telemetry_cls': mock_telemetry_cls,
			'fs_cls': mock_fs_cls,
			'config': mock_config,
		}


@pytest.mark.asyncio
async def test_server_initialization(mock_dependencies):
	server = BrowserUseServer()
	assert server.active_sessions == {}
	assert server.session_timeout_minutes == 10
	mock_dependencies['server_cls'].assert_called_with('browser-use')


@pytest.mark.asyncio
async def test_execute_tool_navigate(mock_dependencies):
	server = BrowserUseServer()
	# Mock initializing browser session
	await server._init_browser_session()

	# Test browser_navigate
	result = await server._execute_tool('browser_navigate', {'url': 'https://example.com'})

	assert 'Navigated to: https://example.com' in result
	mock_dependencies['session'].event_bus.dispatch.assert_called()
	# We can inspect the args if needed


@pytest.mark.asyncio
async def test_execute_tool_click_index(mock_dependencies):
	server = BrowserUseServer()
	await server._init_browser_session()

	# Mock get_dom_element_by_index
	mock_element = EnhancedDOMTreeNode(
		node_id=1,
		backend_node_id=1,
		node_type=NodeType.ELEMENT_NODE,
		node_name='BUTTON',
		node_value='',
		attributes={'id': 'btn1'},
		is_scrollable=False,
		is_visible=True,
		absolute_position=DOMRect(x=0, y=0, width=10, height=10),
		target_id='target1',
		frame_id='frame1',
		session_id='session1',
		content_document=None,
		shadow_root_type=None,
		shadow_roots=None,
		parent_node=None,
		children_nodes=[],
		ax_node=None,
		snapshot_node=None,
	)
	mock_dependencies['session'].get_dom_element_by_index.return_value = mock_element

	# Test browser_click
	result = await server._execute_tool('browser_click', {'index': 1})

	assert 'Clicked element 1' in result
	mock_dependencies['session'].get_dom_element_by_index.assert_called_with(1)


@pytest.mark.asyncio
async def test_execute_tool_click_coordinates(mock_dependencies):
	server = BrowserUseServer()
	await server._init_browser_session()

	# Test browser_click with coordinates
	result = await server._execute_tool('browser_click', {'coordinate_x': 100, 'coordinate_y': 200})

	assert 'Clicked at coordinates (100, 200)' in result
	mock_dependencies['session'].event_bus.dispatch.assert_called()


@pytest.mark.asyncio
async def test_execute_tool_type(mock_dependencies):
	server = BrowserUseServer()
	await server._init_browser_session()

	mock_element = EnhancedDOMTreeNode(
		node_id=1,
		backend_node_id=1,
		node_type=NodeType.ELEMENT_NODE,
		node_name='INPUT',
		node_value='',
		attributes={'id': 'inp1'},
		is_scrollable=False,
		is_visible=True,
		absolute_position=DOMRect(x=0, y=0, width=10, height=10),
		target_id='target1',
		frame_id='frame1',
		session_id='session1',
		content_document=None,
		shadow_root_type=None,
		shadow_roots=None,
		parent_node=None,
		children_nodes=[],
		ax_node=None,
		snapshot_node=None,
	)
	mock_dependencies['session'].get_dom_element_by_index.return_value = mock_element

	# Test browser_type
	result = await server._execute_tool('browser_type', {'index': 1, 'text': 'hello'})

	assert "Typed 'hello' into element 1" in result


@pytest.mark.asyncio
async def test_execute_tool_agent(mock_dependencies):
	server = BrowserUseServer()

	# Setup agent mock return values
	history_mock = MagicMock()
	history_mock.is_successful.return_value = True
	history_mock.history = [1, 2, 3]  # 3 steps
	history_mock.final_result.return_value = 'Done'
	history_mock.errors.return_value = []
	history_mock.urls.return_value = []

	mock_dependencies['agent'].run.return_value = history_mock

	# Test retry_with_browser_use_agent
	result = await server._execute_tool('retry_with_browser_use_agent', {'task': 'do something'})

	assert 'Task completed in 3 steps' in result
	assert 'Success: True' in result
	assert 'Final result:\nDone' in result

	mock_dependencies['agent_cls'].assert_called()


@pytest.mark.asyncio
async def test_execute_tool_unknown(mock_dependencies):
	server = BrowserUseServer()
	result = await server._execute_tool('unknown_tool', {})
	assert 'Unknown tool: unknown_tool' in result


@pytest.mark.asyncio
async def test_session_management(mock_dependencies):
	server = BrowserUseServer()

	# Init session
	await server._init_browser_session()
	assert len(server.active_sessions) == 1
	session_id = mock_dependencies['session'].id

	# List sessions
	sessions = await server._execute_tool('browser_list_sessions', {})
	sessions_data = json.loads(sessions)
	assert len(sessions_data) == 1
	assert sessions_data[0]['session_id'] == session_id

	# Close session
	# We need to simulate the session object supporting kill or close
	# The mock session already has kill mocked

	result = await server._execute_tool('browser_close_session', {'session_id': session_id})
	assert 'Successfully closed session' in result
	assert len(server.active_sessions) == 0
	mock_dependencies['session'].kill.assert_called_once()


@pytest.mark.asyncio
async def test_execute_tool_get_state(mock_dependencies):
	server = BrowserUseServer()
	await server._init_browser_session()

	# Mock state
	mock_state = MagicMock()
	mock_state.url = 'https://example.com'
	mock_state.title = 'Example'
	mock_state.tabs = []
	mock_state.page_info = None
	mock_state.dom_state.selector_map = {}
	mock_state.screenshot = None

	mock_dependencies['session'].get_browser_state_summary.return_value = mock_state

	result = await server._execute_tool('browser_get_state', {})
	state_data = json.loads(result)

	assert state_data['url'] == 'https://example.com'
	assert state_data['title'] == 'Example'


@pytest.mark.asyncio
async def test_execute_tool_scroll(mock_dependencies):
	server = BrowserUseServer()
	await server._init_browser_session()

	result = await server._execute_tool('browser_scroll', {'direction': 'down'})
	assert 'Scrolled down' in result
	mock_dependencies['session'].event_bus.dispatch.assert_called()


@pytest.mark.asyncio
async def test_execute_tool_go_back(mock_dependencies):
	server = BrowserUseServer()
	await server._init_browser_session()

	result = await server._execute_tool('browser_go_back', {})
	assert 'Navigated back' in result
	mock_dependencies['session'].event_bus.dispatch.assert_called()


@pytest.mark.asyncio
async def test_execute_tool_switch_tab(mock_dependencies):
	server = BrowserUseServer()
	await server._init_browser_session()

	mock_dependencies['session'].get_target_id_from_tab_id.return_value = 'target-123'
	mock_state = MagicMock()
	mock_state.url = 'https://tab2.com'
	mock_dependencies['session'].get_browser_state_summary.return_value = mock_state

	result = await server._execute_tool('browser_switch_tab', {'tab_id': '1234'})

	assert 'Switched to tab 1234' in result
	mock_dependencies['session'].event_bus.dispatch.assert_called()


@pytest.mark.asyncio
async def test_execute_tool_close_tab(mock_dependencies):
	server = BrowserUseServer()
	await server._init_browser_session()

	mock_dependencies['session'].get_target_id_from_tab_id.return_value = 'target-123'
	mock_dependencies['session'].get_current_page_url.return_value = 'https://remaining.com'

	result = await server._execute_tool('browser_close_tab', {'tab_id': '1234'})

	assert 'Closed tab # 1234' in result
	mock_dependencies['session'].event_bus.dispatch.assert_called()
