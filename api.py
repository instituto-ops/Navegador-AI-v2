import asyncio
import json
import logging
import os
import time
from typing import Any, cast

import aiofiles
from dotenv import load_dotenv
from fake_useragent import UserAgent
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# browser-use imports
from browser_use import Browser
from browser_use.lam.orchestrator import LAMOrchestrator

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

SYSTEM_PROMPT_EXT = """
IMPORTANT INSTRUCTIONS FOR NAVIGATION:
1. NEVER navigate to relative URLs (e.g., "/product/123"). ALWAYS use absolute URLs (e.g., "https://example.com/product/123").
2. If you find a link on a page, always extract the full href attribute.
3. If a URL is missing the protocol, prepend "https://".
"""


@app.get('/health')
async def health():
	return {'status': 'ok'}


async def get_or_create_browser():
	global shared_browser
	async with shared_browser_lock:
		if shared_browser is None:
			print('[SYSTEM] Inicializando Instância Global do Navegador...')

			# Check for Cloud API Key
			cloud_key = os.getenv('BROWSER_USE_API_KEY')
			if cloud_key:
				print('🚀 [MODE] Using Browser-Use Cloud (Stealth & Anti-Detect)')
				shared_browser = Browser(
					use_cloud=True,
					cloud_profile_id=os.getenv('CLOUD_PROFILE_ID'),  # Optional
				)
			else:
				print('🛡️ [MODE] Using Local Browser (Hardened)')
				abs_profile_path = os.path.abspath(os.path.join(os.getcwd(), 'browser_profile'))  # noqa: ASYNC240
				if not os.path.exists(abs_profile_path):  # noqa: ASYNC240
					os.makedirs(abs_profile_path)

				# Cross-platform executable detection
				chrome_path = os.getenv('BROWSER_EXECUTABLE_PATH')
				if not chrome_path:
					# Fallback for Windows
					for p in [
						r'C:\Program Files\Google\Chrome\Application\chrome.exe',
						r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
					]:
						if os.path.exists(p):  # noqa: ASYNC240
							chrome_path = p
							break

				# User Agent Rotation
				try:
					ua = UserAgent()
					user_agent = ua.random
				except Exception:
					user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

				print(f'🎭 [STEALTH] User-Agent: {user_agent}')

				is_headless = os.getenv('HEADLESS', 'false').lower() == 'true'
				shared_browser = Browser(
					headless=is_headless,
					keep_alive=True,
					executable_path=chrome_path,
					user_data_dir=abs_profile_path,
					user_agent=user_agent,
					args=[
						'--disable-blink-features=AutomationControlled',
						'--no-sandbox',
						'--disable-infobars',
						'--window-size=1280,720',
					],
				)

		return shared_browser


@app.post('/open-browser')
async def open_browser():
	try:
		await get_or_create_browser()
		return {'status': 'success', 'message': 'Navegador ativo'}
	except Exception as e:
		return {'status': 'error', 'message': str(e)}


@app.post('/run-agent')
async def run_agent(request: CommandRequest):
	global current_agent_task
	print(f'\n--- [AGENT] Recebido comando: {request.command} (Modelo: {request.model}) ---')

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

		async def run_task():
			nonlocal start_time
			try:
				browser = await get_or_create_browser()

				# Instantiate LAM Orchestrator
				# Determine model based on request (simplified logic here)
				model_name = 'gpt-4o'
				if request.model == 'ollama':
					model_name = 'ollama/llama3.2'
				elif request.model == 'smol':
					model_name = 'ollama/qwen2.5:3b'

				# If user specifically requests a model in the command or context, we might want to pass it
				# For now, sticking to request.model mapping

				orchestrator = LAMOrchestrator(browser=browser, model_name=model_name)

				# Use astream instead of run directly on orchestrator because orchestrator.run is an async generator
				async for event in orchestrator.run(request.command):
					elapsed = round(time.time() - start_time, 1)

					if 'planner' in event:
						plan_data = event['planner'].get('plan', [])
						plan_text = '\\n'.join([f'{i + 1}. {step.get("description")}' for i, step in enumerate(plan_data)])
						await queue.put({'type': 'info', 'message': f'📝 Plano gerado:\\n{plan_text}', 'elapsed': elapsed})

					if 'executor' in event:
						# In LangGraph with annotated state, results list grows.
						# We want to show the LATEST result.
						# But the event usually contains the output of the node execution.
						# Our executor_node returns {"results": [new_result]}.
						# So event['executor']['results'] is a list containing only the new result(s).

						exec_results = event['executor'].get('results', [])
						for res in exec_results:
							step_info = res.get('step', {})
							outcome = res.get('outcome', 'Unknown')
							history = res.get('history')

							screenshot_b64 = None
							# Try to extract screenshot from history safely
							try:
								if history and hasattr(history, 'history') and history.history:
									last_item = history.history[-1]
									if hasattr(last_item, 'result') and last_item.result:
										# Result is a list of ActionResult
										# Check if any has base64_image? No, usually screenshot is on state
										pass
									# Or maybe screenshot is stored on the state object inside history?
									# browser-use internal structure varies.
									# Let's assume for now we don't have it easily unless we modify LogicExecutor to return it explicitly.
									pass
							except Exception:
								pass

							await queue.put(
								{
									'type': 'step',
									'step': step_info.get('description', 'Action'),
									'thought': f'Executed: {step_info.get("action_type")} - {outcome}',
									'goal': step_info.get('description'),
									'memory': f'Result: {str(res.get("result"))[:100]}...',
									'url': '...',
									'elapsed': elapsed,
									'screenshot': screenshot_b64,
								}
							)

					if 'summarizer' in event:
						summary = event['summarizer'].get('final_output', 'Done')
						final_url = 'about:blank'
						try:
							if browser:
								page = await browser.get_current_page()
								# Cast to Any to access url if pyright complains about Page type
								if page:
									final_url = cast(Any, page).url
						except:
							pass

						await queue.put(
							{
								'type': 'done',
								'message': 'Tarefa finalizada.',
								'final_url': final_url,
								'summary': summary,
								'total_time': elapsed,
							}
						)

			except Exception as e:
				await queue.put({'type': 'error', 'message': f'Erro fatal: {str(e)}'})
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
		reports_dir = 'reports'
		if not os.path.exists(reports_dir):  # noqa: ASYNC240
			os.makedirs(reports_dir)
		return {'reports': os.listdir(reports_dir)}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@app.get('/reports/{filename}')
async def get_report(filename: str):
	try:
		path = os.path.join('reports', filename)
		async with aiofiles.open(path, encoding='utf-8') as f:
			content = await f.read()
		return {'content': content}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


if __name__ == '__main__':
	import uvicorn

	uvicorn.run(app, host='0.0.0.0', port=8000)
