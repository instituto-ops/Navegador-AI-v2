import asyncio
import json
import logging
import os
import time
import traceback
from typing import Any

from anyio import Path
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
			try:
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
			except Exception as e:
				print(f'[ERROR] Falha crítica ao inicializar navegador: {e}')
				traceback.print_exc()
				raise e

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
		queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

		# technical logging redirect
		logger = logging.getLogger('browser_use')
		logger.setLevel(logging.INFO)
		handler = SSELogHandler(queue, loop, start_time)
		handler.setFormatter(logging.Formatter('%(message)s'))
		logger.addHandler(handler)

		async def run_task():
			nonlocal start_time
			try:
				browser_instance = await get_or_create_browser()

				# Instantiate LAM Orchestrator
				# Determine model based on request (mapping frontend strings to LAM prefixes)
				model_name = 'gpt-4o'  # Default
				if request.model == 'ollama':
					model_name = 'ollama/llama3.2'
				elif request.model == 'smol':
					model_name = 'ollama/qwen2.5:3b'
				elif request.model == 'groq':
					model_name = 'groq/llama-3.3-70b-versatile'
				elif request.model == 'openrouter':
					model_name = 'openrouter/meta-llama/llama-3.3-70b-instruct:free'
				elif request.model == 'puter':
					# Puter "Luxury Fallback" - Using Gemini 2.0 via OpenRouter as it matches Puter's promise
					model_name = 'openrouter/google/gemini-2.0-flash-001'
					await queue.put({'type': 'info', 'message': '💎 Usando Puter (Gemini 2.0 Luxury Fallback)...', 'elapsed': 0})
				elif request.model == 'vision':
					model_name = 'gpt-4o'  # Primary vision model
				elif request.model == 'auto':
					# Attempt to use primary model from .env if auto is selected
					primary = os.getenv('PRIMARY_MODEL', 'groq')
					if primary == 'groq':
						model_name = 'groq/llama-3.3-70b-versatile'
					elif primary == 'openrouter':
						model_name = 'openrouter/meta-llama/llama-3.3-70b-instruct:free'

				print(f'[SYSTEM] Model selected for LAM: {model_name}')

				orchestrator = LAMOrchestrator(browser=browser_instance, model_name=model_name)

				# Use astream instead of run directly on orchestrator because orchestrator.run is an async generator
				async for event in orchestrator.run(request.command):
					now = time.time()
					elapsed = float(round(now - start_time, 1))

					if 'planner' in event:
						plan_data = event['planner'].get('plan', [])
						plan_text = '\n'.join([f'{i + 1}. {step.get("description")}' for i, step in enumerate(plan_data)])
						await queue.put({'type': 'info', 'message': f'📝 Plano gerado:\n{plan_text}', 'elapsed': elapsed})

					if 'executor' in event:
						exec_results = event['executor'].get('results', [])
						for res in exec_results:
							step_info = res.get('step', {})
							outcome = res.get('outcome', 'Unknown')
							history = res.get('history')

							screenshot_b64 = None
							# Extract screenshot from the latest state if possible
							try:
								# Version 0.11.13 might have different state access
								current_page = await browser_instance.get_current_page()
								if current_page:
									# type and full_page are keyword arguments
									screenshot_b64 = await current_page.screenshot(type='jpeg', quality=50, full_page=False)
									import base64

									if isinstance(screenshot_b64, bytes):
										screenshot_b64 = base64.b64encode(screenshot_b64).decode('utf-8')
							except Exception as e:
								print(f'[DEBUG] Screenshot failed: {e}')

							res_val = res.get('result')
							res_str = str(res_val) if res_val is not None else ''
							memory_snippet = res_str[:150]

							await queue.put(
								{
									'type': 'step',
									'step': step_info.get('description', 'Action'),
									'thought': f'Executed: {step_info.get("action_type")} - {outcome}',
									'goal': step_info.get('description'),
									'memory': f'Result: {memory_snippet}',
									'url': '...',
									'elapsed': elapsed,
									'screenshot': screenshot_b64,
								}
							)

					if 'summarizer' in event:
						summary = event['summarizer'].get('final_output', 'Done')
						final_url = 'about:blank'
						try:
							# ROBUST PAGE EXTRACTION
							current_page = await browser_instance.get_current_page()
							if current_page:
								# Access url directly without unnecessary attribute check if we know type
								final_url = current_page.url
						except Exception as e:
							print(f'[DEBUG] Final URL extraction failed: {e}')

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
				traceback.print_exc()
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
			elapsed = float(round(time.time() - self.start_time, 1))
			self.loop.call_soon_threadsafe(
				asyncio.create_task, self.queue.put({'type': 'info', 'message': f'[SYS] {log_entry}', 'elapsed': elapsed})
			)
		except Exception:
			pass


@app.post('/save-logs')
async def save_logs(request: dict):
	try:
		content = request.get('logs', '')
		await Path('last_session_logs.txt').write_text(content, encoding='utf-8')
		return {'status': 'success'}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@app.get('/reports')
async def list_reports():
	try:
		reports_dir = Path('reports')
		if not await reports_dir.exists():
			await reports_dir.mkdir()
		reports = [p.name async for p in reports_dir.iterdir()]
		return {'reports': reports}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@app.get('/reports/{filename}')
async def get_report(filename: str):
	reports_dir = await Path('reports').resolve()
	file_path = reports_dir / filename
	try:
		file_path = await file_path.resolve()
	except OSError:
		raise HTTPException(status_code=403, detail='Acesso negado: O caminho solicitado é inválido.')

	# Security check: Ensure the file path is within the reports directory
	try:
		if os.path.commonpath([str(reports_dir), str(file_path)]) != str(reports_dir):
			raise HTTPException(status_code=403, detail='Acesso negado: O caminho solicitado é inválido.')
	except ValueError:
		raise HTTPException(status_code=403, detail='Acesso negado: O caminho solicitado é inválido.')

	if not await file_path.exists() or not await file_path.is_file():
		raise HTTPException(status_code=404, detail='Relatório não encontrado.')

	try:
		content = await file_path.read_text(encoding='utf-8')
		return {'content': content}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


if __name__ == '__main__':
	import uvicorn

	uvicorn.run(app, host='0.0.0.0', port=8000)
