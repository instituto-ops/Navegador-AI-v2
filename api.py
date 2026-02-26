import asyncio
import json
import logging
import os
import time

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
			print('[SYSTEM] Inicializando Instância Global do Navegador...')
			abs_profile_path = os.path.abspath(os.path.join(os.getcwd(), 'browser_profile'))
			if not os.path.exists(abs_profile_path):
				os.makedirs(abs_profile_path)

			chrome_path = None
			for p in [
				r'C:\Program Files\Google\Chrome\Application\chrome.exe',
				r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
			]:
				if os.path.exists(p):
					chrome_path = p
					break

			profile = BrowserProfile(
				user_data_dir=abs_profile_path,
				headless=False,
				executable_path=chrome_path,
				keep_alive=True,  # Manter vivo após a tarefa
			)
			shared_browser = Browser(browser_profile=profile)
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

				# Seleção de modelos (v5.3.1 logic)
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
								'message': f'🤖 Tentativa {i + 1}: {candidate["name"]} [Instância Compartilhada]',
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

						# O Agente usará uma aba no browser já aberto
						history = await agent.run()

						final_url = 'about:blank'
						try:
							final_url = await browser.get_current_page_url()
						except:
							pass

						summary = 'Tarefa finalizada.'
						if history and history.history:
							last_item = history.history[-1]
							if last_item.result and last_item.result[-1].extracted_content:
								summary = last_item.result[-1].extracted_content

						await queue.put(
							{
								'type': 'done',
								'message': f'Concluído via {candidate["name"]}',
								'final_url': final_url,
								'summary': summary,
								'total_time': round(time.time() - start_time, 1),
							}
						)
						return
					except asyncio.CancelledError:
						await queue.put({'type': 'info', 'message': 'Operação interrompida.'})
						return
					except Exception as e:
						print(f'Erro na tentativa {i + 1}: {e}')
						last_error = e
						continue

				await queue.put({'type': 'error', 'message': f'Falha: {str(last_error)}'})
			except Exception as e:
				await queue.put({'type': 'error', 'message': f'Erro fatal: {str(e)}'})
			finally:
				# REMOVIDO: browser.close() - O navegador permanece aberto para a próxima tarefa
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
		with open('last_session_logs.txt', 'w', encoding='utf-8') as f:
			f.write(content)
		return {'status': 'success'}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@app.get('/reports')
async def list_reports():
	try:
		reports_dir = 'reports'
		await asyncio.to_thread(os.makedirs, reports_dir, exist_ok=True)
		files = await asyncio.to_thread(os.listdir, reports_dir)
		return {'reports': files}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@app.get('/reports/{filename}')
async def get_report(filename: str):
	try:
		path = os.path.join('reports', filename)
		with open(path, 'r', encoding='utf-8') as f:
			content = f.read()
		return {'content': content}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


if __name__ == '__main__':
	import uvicorn

	uvicorn.run(app, host='0.0.0.0', port=8000)
