import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, ANY
from browser_use.mcp.client import MCPClient
from browser_use.tools.service import Tools

@pytest.fixture
def mock_tools():
    tools = MagicMock(spec=Tools)
    tools.registry = MagicMock()
    # Mock the action decorator
    def action_decorator(description=None, **kwargs):
        def decorator(func):
            return func
        return decorator
    tools.registry.action.side_effect = action_decorator
    return tools

@pytest.fixture
def mock_mcp_session():
    session = AsyncMock()
    session.initialize = AsyncMock()
    session.list_tools = AsyncMock()
    session.call_tool = AsyncMock()
    return session

@pytest.fixture
def mock_stdio_client():
    with patch('browser_use.mcp.client.stdio_client') as mock:
        yield mock

@pytest.mark.asyncio
async def test_mcp_client_init():
    client = MCPClient(server_name="test-server", command="echo", args=["hello"])
    assert client.server_name == "test-server"
    assert client.command == "echo"
    assert client.args == ["hello"]
    assert client._connected is False

@pytest.mark.asyncio
async def test_connect_success(mock_stdio_client, mock_mcp_session):
    # Setup mocks
    mock_stdio_ctx = AsyncMock()
    mock_stdio_client.return_value = mock_stdio_ctx
    mock_stdio_ctx.__aenter__.return_value = (AsyncMock(), AsyncMock())

    with patch('browser_use.mcp.client.ClientSession') as MockSession:
        MockSession.return_value = mock_mcp_session
        mock_mcp_session.__aenter__.return_value = mock_mcp_session

        # Setup tools response
        mock_tool = MagicMock()
        mock_tool.name = "test_tool"
        mock_tool.description = "Test Tool"
        mock_tool.inputSchema = {"type": "object", "properties": {"arg": {"type": "string"}}}

        mock_tools_response = MagicMock()
        mock_tools_response.tools = [mock_tool]
        mock_mcp_session.list_tools.return_value = mock_tools_response

        client = MCPClient(server_name="test-server", command="echo")

        # We need to manually trigger the disconnect event or rely on task cancellation
        # But connect() only waits for _connected to be True
        await client.connect()

        assert client._connected is True
        assert "test_tool" in client._tools
        mock_mcp_session.initialize.assert_awaited_once()

        # Cleanup
        await client.disconnect()

@pytest.mark.asyncio
async def test_register_to_tools(mock_stdio_client, mock_mcp_session, mock_tools):
    # Setup connection first
    mock_stdio_ctx = AsyncMock()
    mock_stdio_client.return_value = mock_stdio_ctx
    mock_stdio_ctx.__aenter__.return_value = (AsyncMock(), AsyncMock())

    with patch('browser_use.mcp.client.ClientSession') as MockSession:
        MockSession.return_value = mock_mcp_session
        mock_mcp_session.__aenter__.return_value = mock_mcp_session

        mock_tool = MagicMock()
        mock_tool.name = "test_tool"
        mock_tool.description = "Test Tool"
        mock_tool.inputSchema = {"type": "object", "properties": {"arg": {"type": "string"}}}

        mock_tools_response = MagicMock()
        mock_tools_response.tools = [mock_tool]
        mock_mcp_session.list_tools.return_value = mock_tools_response

        client = MCPClient(server_name="test-server", command="echo")
        await client.register_to_tools(mock_tools)

        assert client._connected is True
        mock_tools.registry.action.assert_called()

        # Verify the registered action wrapper
        args, kwargs = mock_tools.registry.action.call_args
        assert kwargs['description'] == "Test Tool"

        await client.disconnect()

@pytest.mark.asyncio
async def test_tool_execution(mock_stdio_client, mock_mcp_session, mock_tools):
    # Capture the wrapper function
    captured_wrapper = None

    def action_decorator(description=None, **kwargs):
        def decorator(func):
            nonlocal captured_wrapper
            captured_wrapper = func
            return func
        return decorator

    mock_tools.registry.action.side_effect = action_decorator

    # Setup connection
    mock_stdio_ctx = AsyncMock()
    mock_stdio_client.return_value = mock_stdio_ctx
    mock_stdio_ctx.__aenter__.return_value = (AsyncMock(), AsyncMock())

    with patch('browser_use.mcp.client.ClientSession') as MockSession:
        MockSession.return_value = mock_mcp_session
        mock_mcp_session.__aenter__.return_value = mock_mcp_session

        mock_tool = MagicMock()
        mock_tool.name = "test_tool"
        mock_tool.inputSchema = {"type": "object", "properties": {"arg": {"type": "string"}}}

        mock_tools_response = MagicMock()
        mock_tools_response.tools = [mock_tool]
        mock_mcp_session.list_tools.return_value = mock_tools_response

        mock_mcp_session.call_tool.return_value = MagicMock(content=[MagicMock(text="Tool Result")])

        client = MCPClient(server_name="test-server", command="echo")
        await client.register_to_tools(mock_tools)

        assert captured_wrapper is not None

        # Get the param model class
        call_args = mock_tools.registry.action.call_args
        param_model_cls = call_args[1].get('param_model')

        params = param_model_cls(arg="value")

        # Call the wrapper
        result = await captured_wrapper(params)

        assert result.extracted_content == "Tool Result"
        mock_mcp_session.call_tool.assert_awaited_with("test_tool", {"arg": "value"})

        await client.disconnect()

@pytest.mark.asyncio
async def test_tool_execution_no_params(mock_stdio_client, mock_mcp_session, mock_tools):
    captured_wrapper = None

    def action_decorator(description=None, **kwargs):
        def decorator(func):
            nonlocal captured_wrapper
            captured_wrapper = func
            return func
        return decorator

    mock_tools.registry.action.side_effect = action_decorator

    mock_stdio_ctx = AsyncMock()
    mock_stdio_client.return_value = mock_stdio_ctx
    mock_stdio_ctx.__aenter__.return_value = (AsyncMock(), AsyncMock())

    with patch('browser_use.mcp.client.ClientSession') as MockSession:
        MockSession.return_value = mock_mcp_session
        mock_mcp_session.__aenter__.return_value = mock_mcp_session

        mock_tool = MagicMock()
        mock_tool.name = "no_param_tool"
        mock_tool.inputSchema = {} # No properties

        mock_tools_response = MagicMock()
        mock_tools_response.tools = [mock_tool]
        mock_mcp_session.list_tools.return_value = mock_tools_response

        mock_mcp_session.call_tool.return_value = MagicMock(content=[MagicMock(text="No Param Result")])

        client = MCPClient(server_name="test-server", command="echo")
        await client.register_to_tools(mock_tools)

        assert captured_wrapper is not None

        # Verify param_model is None or empty?
        # Code says: if param_fields: ... else: param_model = None
        call_args = mock_tools.registry.action.call_args
        param_model = call_args[1].get('param_model')
        assert param_model is None

        # Call the wrapper with no args
        result = await captured_wrapper()

        assert result.extracted_content == "No Param Result"
        mock_mcp_session.call_tool.assert_awaited_with("no_param_tool", {})

        await client.disconnect()

@pytest.mark.asyncio
async def test_connect_failure(mock_stdio_client):
    # Simulate connection failing to establish (timeout)
    # We mock stdio_client to raise error or just hang?
    # connect() waits for self._connected to be true.

    # If _run_stdio_client fails immediately, it raises exception.
    # connect() catches it via create_task_with_error_handling? No, create_task_with_error_handling suppresses exceptions.
    # Wait, create_task_with_error_handling(..., suppress_exceptions=True)

    # But connect() waits for _connected in a loop with timeout.

    mock_stdio_ctx = AsyncMock()
    mock_stdio_client.return_value = mock_stdio_ctx
    # Make __aenter__ raise exception
    mock_stdio_ctx.__aenter__.side_effect = Exception("Connection failed")

    client = MCPClient(server_name="test-server", command="echo")

    # We should expect RuntimeError from connect() timeout loop or the exception itself?
    # Since suppress_exceptions=True, the task dies quietly.
    # So connect() loop will timeout.

    # However, to speed up test, we should mock sleep or reduce retries.
    # connect() has max_retries = 100 * 0.1s = 10s.
    # We can patch time.sleep or asyncio.sleep? No it uses asyncio.sleep.

    with patch('asyncio.sleep', new_callable=AsyncMock), \
         pytest.raises(RuntimeError) as excinfo:
         await client.connect()

    assert "Failed to connect to MCP server" in str(excinfo.value)
