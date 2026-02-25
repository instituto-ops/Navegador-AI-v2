from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
from browser_use import Agent, Browser, ChatGroq, ChatMistral, ChatOpenAI
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

app = FastAPI()

# Configurar CORS para permitir que o React se comunique com o Python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CommandRequest(BaseModel):
    command: str

@app.get("/health")
async def health():
    return {"status": "ok"}

from fastapi.responses import StreamingResponse
import json

@app.post("/run-agent")
async def run_agent(request: CommandRequest):
    print(f"\n--- [AGENT] Recebido comando: {request.command} ---")
    
    async def event_generator():
        queue = asyncio.Queue()
        
        async def step_callback(state, output, step):
            await queue.put({
                "type": "step",
                "step": step,
                "thought": getattr(output, 'thinking', '') or '',
                "goal": getattr(output, 'next_goal', '') or '',
                "memory": getattr(output, 'memory', '') or '',
                "url": state.url
            })

        async def run_task():
            try:
                # 1. Groq (Llama 3.3 - Alta velocidade)
                llm_candidates = []
                groq_key = os.getenv("GROQ_API_KEY")
                if groq_key:
                    llm_candidates.append({
                        "name": "Groq (Llama 3.3)",
                        "client": ChatGroq(model="llama-3.3-70b-versatile", api_key=groq_key)
                    })

                or_key = os.getenv("OPENROUTER_API_KEY")
                if or_key:
                    llm_candidates.append({
                        "name": "OpenRouter",
                        "client": ChatOpenAI(
                            model="meta-llama/llama-3.3-70b-instruct:free", 
                            api_key=or_key,
                            base_url="https://openrouter.ai/api/v1"
                        )
                    })

                if not llm_candidates:
                    await queue.put({"type": "error", "message": "Nenhuma API Key encontrada no .env"})
                    return

                browser = Browser(headless=False)
                last_error = None
                
                for i, candidate in enumerate(llm_candidates):
                    try:
                        await queue.put({
                            "type": "info", 
                            "message": f"Tentativa {i+1}: Usando {candidate['name']}..."
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
                        
                        # Resumo das ações
                        action_summary = "Tarefa concluída."
                        if history and history.history:
                            last_item = history.history[-1]
                            if last_item.result and last_item.result[-1].extracted_content:
                                action_summary = last_item.result[-1].extracted_content

                        await queue.put({
                            "type": "done",
                            "message": f"Concluído via {candidate['name']}",
                            "final_url": final_url,
                            "summary": action_summary
                        })
                        return # Sucesso
                    except Exception as e:
                        print(f"Erro na tentativa {i+1}: {e}")
                        last_error = e
                        continue
                
                await queue.put({"type": "error", "message": f"Todas as APIs falharam: {str(last_error)}"})
            except Exception as e:
                await queue.put({"type": "error", "message": str(e)})
            finally:
                await queue.put({"type": "end"}) # Signal end of stream

        # Start the task in background
        task = asyncio.create_task(run_task())
        
        while True:
            item = await queue.get()
            if item.get("type") == "end":
                break
            yield f"data: {json.dumps(item)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/save-logs")
async def save_logs(request: dict):
    try:
        content = request.get("logs", "")
        with open("last_session_logs.txt", "w", encoding="utf-8") as f:
            f.write(content)
        print("[SYSTEM] Logs salvos com sucesso em last_session_logs.txt")
        return {"status": "success", "message": "Logs salvos com sucesso"}
    except Exception as e:
        print(f"[ERROR] Falha ao salvar logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reports")
async def list_reports():
    try:
        reports_dir = "reports"
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)
        files = os.listdir(reports_dir)
        # Filter for text, md, docx files if needed
        return {"reports": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reports/{filename}")
async def get_report(filename: str):
    try:
        path = os.path.join("reports", filename)
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="Relatório não encontrado")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
