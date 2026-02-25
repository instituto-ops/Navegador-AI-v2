from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import time
from browser_use import Agent, Browser, ChatGroq, ChatMistral, ChatOpenAI
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CommandRequest(BaseModel):
    command: str
    model: str = "auto" # 'auto', 'groq', 'ollama', 'openrouter', 'vision'

# Global control for stopping tasks
current_agent_task = None

@app.get("/health")
async def health():
    return {"status": "ok"}

from fastapi.responses import StreamingResponse
import json

@app.post("/run-agent")
async def run_agent(request: CommandRequest):
    global current_agent_task
    print(f"\n--- [AGENT] Recebido comando: {request.command} (Modelo: {request.model}) ---")
    
    start_time = time.time()

    async def event_generator():
        queue = asyncio.Queue()
        
        async def step_callback(state, output, step):
            elapsed = round(time.time() - start_time, 1)
            await queue.put({
                "type": "step",
                "step": step,
                "thought": getattr(output, 'thinking', '') or '',
                "goal": getattr(output, 'next_goal', '') or '',
                "memory": getattr(output, 'memory', '') or '',
                "url": state.url,
                "elapsed": elapsed
            })

        async def run_task():
            nonlocal start_time
            try:
                llm_candidates = []
                or_key = os.getenv("OPENROUTER_API_KEY")
                
                # Configuração de Modelos
                if request.model == "groq" or request.model == "auto":
                    groq_key = os.getenv("GROQ_API_KEY")
                    if groq_key:
                        llm_candidates.append({
                            "name": "Groq (Llama 3.3)",
                            "client": ChatGroq(model="llama-3.3-70b-versatile", api_key=groq_key)
                        })

                if request.model == "vision":
                    # PRIORIDADE 1: OpenRouter (Usa sua chave OR para acessar Gemini/Llama Vision sem chave Google)
                    if or_key:
                        # Llama 3.2 11B Vision no OpenRouter (Geralmente gratuíto ou muito barato)
                        llm_candidates.append({
                            "name": "Cloud Vision (Llama-11B-Free)",
                            "client": ChatOpenAI(
                                model="meta-llama/llama-3.2-11b-vision-instruct:free", 
                                api_key=or_key,
                                base_url="https://openrouter.ai/api/v1"
                            )
                        })
                        # Gemini Flash (Altíssima velocidade e competência visual via OR)
                        llm_candidates.append({
                            "name": "Cloud Vision (Gemini Flash)",
                            "client": ChatOpenAI(
                                model="google/gemini-flash-1.5", 
                                api_key=or_key,
                                base_url="https://openrouter.ai/api/v1"
                            )
                        })
                    
                    # PRIORIDADE 2: Local Vision (Ollama - 100% Grátis e Privado)
                    llm_candidates.append({
                        "name": "Local Vision (Llama-Vision)",
                        "client": ChatOpenAI(
                            model="llama3.2-vision", 
                            api_key="ollama", # placeholder
                            base_url="http://localhost:11434/v1"
                        )
                    })

                if request.model == "openrouter" or (request.model == "auto" and not llm_candidates):
                    if or_key:
                        llm_candidates.append({
                            "name": "OpenRouter Cloud",
                            "client": ChatOpenAI(
                                model="meta-llama/llama-3.3-70b-instruct:free", 
                                api_key=or_key,
                                base_url="https://openrouter.ai/api/v1"
                            )
                        })

                if request.model == "ollama":
                    llm_candidates.append({
                        "name": "Ollama Local",
                        "client": ChatOpenAI(
                            model="llama3.2", 
                            api_key="ollama",
                            base_url="http://localhost:11434/v1"
                        )
                    })

                if not llm_candidates:
                    await queue.put({"type": "error", "message": "Nenhum provedor disponível. Verifique suas chaves no .env."})
                    return

                browser = Browser(headless=False)
                last_error = None
                
                for i, candidate in enumerate(llm_candidates):
                    try:
                        await queue.put({
                            "type": "info", 
                            "message": f"Tentativa {i+1}: Conectando ao {candidate['name']}...",
                            "elapsed": round(time.time() - start_time, 1)
                        })
                        
                        agent = Agent(
                            task=request.command,
                            llm=candidate['client'],
                            browser=browser,
                            use_vision=True,
                            register_new_step_callback=step_callback
                        )

                        history = await agent.run()
                        
                        final_url = "about:blank"
                        try:
                            state = await browser.get_state()
                            final_url = state.url
                        except: pass
                        
                        action_summary = "Tarefa concluída."
                        if history and history.history:
                            last_item = history.history[-1]
                            if last_item.result and last_item.result[-1].extracted_content:
                                action_summary = last_item.result[-1].extracted_content

                        await queue.put({
                            "type": "done",
                            "message": f"Concluído via {candidate['name']}",
                            "final_url": final_url,
                            "summary": action_summary,
                            "total_time": round(time.time() - start_time, 1)
                        })
                        return 
                    except asyncio.CancelledError:
                        await queue.put({"type": "info", "message": "Operação cancelada pelo usuário."})
                        return
                    except Exception as e:
                        print(f"Erro na tentativa {i+1} ({candidate['name']}): {e}")
                        last_error = e
                        continue
                
                await queue.put({"type": "error", "message": f"Falha no processamento: {str(last_error)}"})
            except Exception as e:
                await queue.put({"type": "error", "message": str(e)})
            finally:
                await queue.put({"type": "end"})

        task = asyncio.create_task(run_task())
        current_agent_task = task
        
        try:
            while True:
                item = await queue.get()
                if item.get("type") == "end":
                    break
                yield f"data: {json.dumps(item)}\n\n"
        finally:
            current_agent_task = None

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/stop-agent")
async def stop_agent():
    global current_agent_task
    if current_agent_task and not current_agent_task.done():
        current_agent_task.cancel()
        return {"status": "success"}
    return {"status": "info"}

@app.post("/save-logs")
async def save_logs(request: dict):
    try:
        content = request.get("logs", "")
        with open("last_session_logs.txt", "w", encoding="utf-8") as f:
            f.write(content)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reports")
async def list_reports():
    try:
        reports_dir = "reports"
        if not os.path.exists(reports_dir): os.makedirs(reports_dir)
        return {"reports": os.listdir(reports_dir)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reports/{filename}")
async def get_report(filename: str):
    try:
        path = os.path.join("reports", filename)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
