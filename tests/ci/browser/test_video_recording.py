import pytest
from browser_use.browser.profile import ViewportSize
from browser_use import Agent
from browser_use.browser import BrowserProfile, BrowserSession
from tests.ci.conftest import create_mock_llm


@pytest.fixture
def test_dir(tmp_path):
	test_path = tmp_path / 'test_recordings'
	test_path.mkdir(exist_ok=True)
	yield test_path


@pytest.fixture
def llm():
	return create_mock_llm()


@pytest.mark.asyncio
async def test_video_recording_threading(test_dir, llm):
	"""
	Test that video recording works with the threaded implementation.
	We verify the file is created and has content.
	"""
	# Enable video recording
	profile = BrowserProfile(
		headless=True,
		disable_security=True,
		record_video_dir=test_dir,
		record_video_size=ViewportSize(width=1280, height=720)
	)

	# We use a context manager to ensure proper cleanup
	session = BrowserSession(browser_profile=profile)
	await session.start()

	try:
		agent = Agent(task='go to google.com', llm=llm, browser_session=session)

		# We run the agent for a short time.
		# The mock LLM returns "done" immediately by default, so it might finish too fast to record many frames.
		# But even one frame is enough to verify recording works.
		await agent.run(max_steps=1)

		# We need to ensure session is closed so video is saved
	finally:
		# Close session (which triggers stop_and_save)
		await session.kill()

	# Check if video file exists
	videos = list(test_dir.glob('*.mp4'))
	assert len(videos) > 0, 'No video file created'

	# Check file size > 0
	file_size = videos[0].stat().st_size
	assert file_size > 0, f'Video file is empty, size: {file_size}'

	print(f'Video created: {videos[0]}, size: {file_size}')
