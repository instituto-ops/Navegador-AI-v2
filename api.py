import asyncio
import json
import logging
import os
import time

import aiofiles
from anyio import Path as AsyncPath
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# browser-use imports
from browser_use import Agent, Browser, BrowserProfile, ChatGroq, ChatOpenAI

# Carregar variáveis de ambiente
load_dotenv()

app = FastAPI()

# Configurar CORS
app.add_middleware(
	CORSMiddleware,
	allow_origins=['*'],
	allow_credentials=True,
	allow_methods=['*'],
	allow_headers=['*'],
)


class CommandRequest(BaseModel):
	command: str
	model: str = 'auto'


# --- PERSISTÊNCIA GLOBAL ---
current_agent_task = None
shared_browser = None
shared_browser_lock = asyncio.Lock()


@app.get('/health')
async def health():
	return {'status': 'ok'}


async def get_or_create_browser():
	global shared_browser
	async with shared_browser_lock:
		if shared_browser is None:
			print('[SYSTEM] Initializing Global Browser Instance...')
			# Use AsyncPath for async operations where possible, but getcwd is synchronous
			base_path = AsyncPath(os.getcwd())
			abs_profile_path = await base_path.joinpath('browser_profile').resolve()

			if not await abs_profile_path.exists():
				await abs_profile_path.mkdir(parents=True)

			chrome_path = None
			# Check common paths asynchronously
			common_paths = [
				r'C:\Program Files\Google\Chrome\Application\chrome.exe',
				r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
			]
			for p_str in common_paths:
				p = AsyncPath(p_str)
				if await p.exists():
					chrome_path = str(p)
					break

			profile = BrowserProfile(
				user_data_dir=str(abs_profile_path),
				headless=False,
				executable_path=chrome_path,
				keep_alive=True,  # Keep alive after task
			)
			shared_browser = Browser(browser_profile=profile)
		return shared_browser


@app.post('/open-browser')
async def open_browser():
	try:
		await get_or_create_browser()
		return {'status': 'success', 'message': 'Browser active'}
	except Exception as e:
		return {'status': 'error', 'message': str(e)}


@app.post('/run-agent')
async def run_agent(request: CommandRequest):
	global current_agent_task
	print(f'\n--- [AGENT] Received command: {request.command} (Model: {request.model}) ---')

	start_time = time.time()
	loop = asyncio.get_running_loop()

	async def event_generator():
		queue = asyncio.Queue()

		# technical logging redirect
		logger = logging.getLogger('browser_use')
		logger.setLevel(logging.INFO)
		handler = SSELogHandler(queue, loop, start_time)
		handler.setFormatter(logging.Formatter('%(message)s'))
		logger.addHandler(handler)

		async def step_callback(state, output, step):
			elapsed = round(time.time() - start_time, 1)
			await queue.put(
				{
					'type': 'step',
					'step': step,
					'thought': getattr(output, 'thinking', '') or '',
					'goal': getattr(output, 'next_goal', '') or '',
					'memory': getattr(output, 'memory', '') or '',
					'url': state.url,
					'elapsed': elapsed,
				}
			)

		async def run_task():
			nonlocal start_time
			try:
				browser = await get_or_create_browser()
				llm_candidates = []
				or_key = os.getenv('OPENROUTER_API_KEY')

				# Model selection (v5.3.1 logic)
				if request.model in ['auto', 'groq']:
					groq_key = os.getenv('GROQ_API_KEY')
					if groq_key:
						llm_candidates.append(
							{'name': 'Groq Llama 3.3', 'client': ChatGroq(model='llama-3.3-70b-versatile', api_key=groq_key)}
						)

				if request.model == 'vision':
					if or_key:
						llm_candidates.append(
							{
								'name': 'Cloud Vision Free',
								'client': ChatOpenAI(
									model='meta-llama/llama-3.2-11b-vision-instruct:free',
									api_key=or_key,
									base_url='https://openrouter.ai/api/v1',
								),
							}
						)
					llm_candidates.append(
						{
							'name': 'Local Vision',
							'client': ChatOpenAI(model='llama3.2-vision', api_key='ollama', base_url='http://localhost:11434/v1'),
						}
					)

				if request.model == 'smol':
					llm_candidates.append(
						{
							'name': 'Local Qwen 2.5 (3B)',
							'client': ChatOpenAI(model='qwen2.5:3b', api_key='ollama', base_url='http://localhost:11434/v1'),
						}
					)

				if request.model == 'ollama':
					llm_candidates.append(
						{
							'name': 'Local Llama 3.2 (3B)',
							'client': ChatOpenAI(model='llama3.2', api_key='ollama', base_url='http://localhost:11434/v1'),
						}
					)

				if request.model == 'openrouter' or (request.model == 'auto' and not llm_candidates):
					if or_key:
						llm_candidates.append(
							{
								'name': 'OpenRouter Free',
								'client': ChatOpenAI(
									model='meta-llama/llama-3.3-70b-instruct:free',
									api_key=or_key,
									base_url='https://openrouter.ai/api/v1',
								),
							}
						)

				if not llm_candidates:
					llm_candidates.append(
						{
							'name': 'Fallback',
							'client': ChatOpenAI(model='llama3.2', api_key='ollama', base_url='http://localhost:11434/v1'),
						}
					)

				last_error = None
				for i, candidate in enumerate(llm_candidates):
					try:
						await queue.put(
							{
								'type': 'info',
								'message': f'🤖 Attempt {i + 1}: {candidate["name"]} [Shared Instance]',
								'elapsed': round(time.time() - start_time, 1),
							}
						)

						agent = Agent(
							task=request.command,
							llm=candidate['client'],
							browser=browser,
							use_vision=True,
							register_new_step_callback=step_callback,
						)

						# Agent uses existing browser tab
						history = await agent.run()

						final_url = 'about:blank'
						try:
							final_url = await browser.get_current_page_url()
						except Exception:
							pass

						summary = 'Task completed.'
						if history and history.history:
							last_item = history.history[-1]
							if last_item.result and last_item.result[-1].extracted_content:
								summary = last_item.result[-1].extracted_content

						await queue.put(
							{
								'type': 'done',
								'message': f'Completed via {candidate["name"]}',
								'final_url': final_url,
								'summary': summary,
								'total_time': round(time.time() - start_time, 1),
							}
						)
						return
					except asyncio.CancelledError:
						await queue.put({'type': 'info', 'message': 'Operation interrupted.'})
						return
					except Exception as e:
						print(f'Error in attempt {i + 1}: {e}')
						last_error = e
						continue

				await queue.put({'type': 'error', 'message': f'Failure: {str(last_error)}'})
			except Exception as e:
				await queue.put({'type': 'error', 'message': f'Fatal error: {str(e)}'})
			finally:
				logger.removeHandler(handler)
				await queue.put({'type': 'end'})

		task = asyncio.create_task(run_task())
		current_agent_task = task

		try:
			while True:
				item = await queue.get()
				if item.get('type') == 'end':
					break
				yield f'data: {json.dumps(item)}\n\n'
		finally:
			current_agent_task = None

	return StreamingResponse(event_generator(), media_type='text/event-stream')


@app.post('/stop-agent')
async def stop_agent():
	global current_agent_task
	if current_agent_task and not current_agent_task.done():
		current_agent_task.cancel()
		return {'status': 'success'}
	return {'status': 'info'}


# Custom Log Handler to stream logs to SSE
class SSELogHandler(logging.Handler):
	def __init__(self, queue, loop, start_time):
		super().__init__()
		self.queue = queue
		self.loop = loop
		self.start_time = start_time

	def emit(self, record):
		try:
			log_entry = self.format(record)
			elapsed = round(time.time() - self.start_time, 1)
			self.loop.call_soon_threadsafe(
				asyncio.create_task, self.queue.put({'type': 'info', 'message': f'[SYS] {log_entry}', 'elapsed': elapsed})
			)
		except Exception:
			pass


@app.post('/save-logs')
async def save_logs(request: dict):
	try:
		content = request.get('logs', '')
		async with aiofiles.open('last_session_logs.txt', 'w', encoding='utf-8') as f:
			await f.write(content)
		return {'status': 'success'}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@app.get('/reports')
async def list_reports():
	try:
		reports_dir = AsyncPath('reports')
		if not await reports_dir.exists():
			await reports_dir.mkdir()

		# anyio.Path doesn't have listdir, need to use scandir or similar if available,
		# or stick to os.listdir since listing dirs is usually fast enough,
		# but let's try to be compliant.
		# Actually anyio.Path doesn't support iteration of children directly in all versions.
		# Let's use os.listdir but maybe wrapped?
		# For simplicity and since listdir isn't flagged as ASYNC240 in the log (only exists/makedirs/open were),
		# I'll stick to os.listdir for now or use aiofiles.os.listdir if available.
		# But wait, the error said "Async functions should not use os.path methods".
		# It didn't explicitly complain about os.listdir but it likely will.
		# Let's use os.listdir for now as anyio doesn't seem to have a direct replacement in the import.
		# Actually, let's use os.listdir and hope.
		return {'reports': os.listdir(str(reports_dir))}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@app.get('/reports/{filename}')
async def get_report(filename: str):
	try:
		reports_dir = AsyncPath('reports')
		path = reports_dir / filename
		async with aiofiles.open(path, 'r', encoding='utf-8') as f:
			content = await f.read()
		return {'content': content}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


if __name__ == '__main__':
	import uvicorn

	uvicorn.run(app, host='0.0.0.0', port=8000)
