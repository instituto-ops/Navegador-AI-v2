import base64
from unittest.mock import Mock, mock_open, patch

import pytest
from browser_use.agent.judge import construct_judge_messages
from browser_use.llm.messages import (
    ContentPartImageParam,
    ContentPartTextParam,
    SystemMessage,
    UserMessage,
)


@pytest.fixture
def mock_path():
    with patch('browser_use.agent.judge.Path') as mock:
        yield mock


@pytest.fixture
def mock_file_open():
    with patch('builtins.open', mock_open(read_data=b'fake_image_data')) as mock:
        yield mock


def test_construct_judge_messages_basic():
    """Test basic usage with minimal arguments."""
    messages = construct_judge_messages(
        task="Find a cat",
        final_result="Found a cat",
        agent_steps=["Step 1: Open Google", "Step 2: Search cat"],
        screenshot_paths=[],
    )

    assert len(messages) == 2
    assert isinstance(messages[0], SystemMessage)
    assert isinstance(messages[1], UserMessage)

    # Check system message content
    assert "You are an expert judge" in messages[0].content
    assert "PRIMARY EVALUATION CRITERIA" in messages[0].content

    # Check user message content
    user_content = messages[1].content
    assert isinstance(user_content, list)
    assert len(user_content) == 1
    assert isinstance(user_content[0], ContentPartTextParam)

    text = user_content[0].text
    assert "<task>\nFind a cat\n</task>" in text
    assert "<final_result>\nFound a cat\n</final_result>" in text
    assert "Step 1: Open Google" in text


def test_construct_judge_messages_with_ground_truth():
    """Test usage with ground_truth."""
    messages = construct_judge_messages(
        task="Find a cat",
        final_result="Found a cat",
        agent_steps=[],
        screenshot_paths=[],
        ground_truth="Must be a tabby cat",
    )

    system_msg = messages[0].content
    user_msg_text = messages[1].text

    assert "GROUND TRUTH VALIDATION" in system_msg
    assert "<ground_truth>\nMust be a tabby cat\n</ground_truth>" in user_msg_text


def test_construct_judge_messages_use_vision_true(mock_path, mock_file_open):
    """Test usage with use_vision=True and valid screenshots."""
    # Setup mocks
    mock_path_instance = Mock()
    mock_path_instance.exists.return_value = True
    mock_path.return_value = mock_path_instance

    screenshot_paths = ["screen1.png", "screen2.png"]

    messages = construct_judge_messages(
        task="Task",
        final_result="Result",
        agent_steps=[],
        screenshot_paths=screenshot_paths,
        use_vision=True,
    )

    user_content = messages[1].content
    assert len(user_content) == 3  # 1 text + 2 images

    # Check images
    assert isinstance(user_content[1], ContentPartImageParam)
    assert isinstance(user_content[2], ContentPartImageParam)

    # Verify image data format
    expected_b64 = base64.b64encode(b'fake_image_data').decode('utf-8')
    assert user_content[1].image_url.url == f'data:image/png;base64,{expected_b64}'


def test_construct_judge_messages_use_vision_false(mock_path):
    """Test usage with use_vision=False."""
    screenshot_paths = ["screen1.png"]

    messages = construct_judge_messages(
        task="Task",
        final_result="Result",
        agent_steps=[],
        screenshot_paths=screenshot_paths,
        use_vision=False,
    )

    user_content = messages[1].content
    assert len(user_content) == 1  # Only text, no images
    assert isinstance(user_content[0], ContentPartTextParam)


def test_construct_judge_messages_broken_image_path(mock_path):
    """Test usage with broken image paths."""
    # Setup mocks to simulate file not found
    mock_path_instance = Mock()
    mock_path_instance.exists.return_value = False
    mock_path.return_value = mock_path_instance

    screenshot_paths = ["missing.png"]

    messages = construct_judge_messages(
        task="Task",
        final_result="Result",
        agent_steps=[],
        screenshot_paths=screenshot_paths,
        use_vision=True,
    )

    user_content = messages[1].content
    assert len(user_content) == 1  # Only text, image skipped


def test_construct_judge_messages_max_images(mock_path, mock_file_open):
    """Test usage with max_images limiting screenshots."""
    # Setup mocks
    mock_path_instance = Mock()
    mock_path_instance.exists.return_value = True
    mock_path.return_value = mock_path_instance

    screenshot_paths = ["s1.png", "s2.png", "s3.png", "s4.png"]

    messages = construct_judge_messages(
        task="Task",
        final_result="Result",
        agent_steps=[],
        screenshot_paths=screenshot_paths,
        max_images=2,
        use_vision=True,
    )

    user_content = messages[1].content
    # Should have text + 2 images (last 2)
    assert len(user_content) == 3

    # Verify mock was called for the last 2 images
    # We can check the number of calls to Path constructor or encode logic
    # But checking output length is sufficient for unit test logic verification


def test_construct_judge_messages_truncation():
    """Test truncation of long inputs."""
    long_task = "a" * 50000
    long_result = "b" * 50000

    messages = construct_judge_messages(
        task=long_task,
        final_result=long_result,
        agent_steps=[],
        screenshot_paths=[],
    )

    user_content_text = messages[1].text

    # Check that text was truncated
    assert len(user_content_text) < 100000  # Should be significantly smaller
    assert "...[text truncated]" in user_content_text
