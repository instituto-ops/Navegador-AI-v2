# pyright: reportMissingImports=false
import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv

load_dotenv()

# Third-party imports
import gradio as gr  # type: ignore

# Local module imports
from browser_use import Agent, ChatOpenAI
from browser_use.agent.views import AgentHistoryList


def parse_agent_result(history: AgentHistoryList) -> str:
	summary = []

	# Check if the task was marked as successful
	is_success = history.is_successful()
	final_result = history.final_result()
	errors = history.errors()
	model_actions = history.model_actions()

	# Filter out None errors
	real_errors = [e for e in errors if e]

	if is_success:
		summary.append('✅ Task Completed Successfully')
		if final_result:
			summary.append(f'Result: {final_result}')
		else:
			summary.append('No specific result content returned.')
	elif is_success is False:
		summary.append('❌ Task Failed')
		if final_result:
			summary.append(f'Failure Reason: {final_result}')
	else:
		summary.append('⚠️ Task Incomplete')
		if final_result:
			summary.append(f'Last Result: {final_result}')

	if real_errors:
		summary.append('\nErrors encountered:')
		for i, error in enumerate(real_errors[-3:], 1):
			summary.append(f'{i}. {error}')

	if model_actions:
		summary.append(f'\nSteps executed: {len(model_actions)}')

	return '\n'.join(summary)


async def run_browser_task(
	task: str,
	api_key: str,
	model: str = 'gpt-4.1',
	headless: bool = True,
) -> str:
	if not api_key.strip():
		return 'Please provide an API key'

	os.environ['OPENAI_API_KEY'] = api_key

	try:
		agent = Agent(
			task=task,
			llm=ChatOpenAI(model='gpt-4.1-mini'),
		)
		result = await agent.run()
		return parse_agent_result(result)
	except Exception as e:
		return f'Error: {str(e)}'


def create_ui():
	with gr.Blocks(title='Browser Use GUI') as interface:
		gr.Markdown('# Browser Use Task Automation')

		with gr.Row():
			with gr.Column():
				api_key = gr.Textbox(label='OpenAI API Key', placeholder='sk-...', type='password')
				task = gr.Textbox(
					label='Task Description',
					placeholder='E.g., Find flights from New York to London for next week',
					lines=3,
				)
				model = gr.Dropdown(choices=['gpt-4.1-mini', 'gpt-5', 'o3', 'gpt-5-mini'], label='Model', value='gpt-4.1-mini')
				headless = gr.Checkbox(label='Run Headless', value=False)
				submit_btn = gr.Button('Run Task')

			with gr.Column():
				output = gr.Textbox(label='Output', lines=10, interactive=False)

		submit_btn.click(
			fn=lambda *args: asyncio.run(run_browser_task(*args)),
			inputs=[task, api_key, model, headless],
			outputs=output,
		)

	return interface


if __name__ == '__main__':
	demo = create_ui()
	demo.launch()
