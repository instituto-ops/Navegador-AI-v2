import React, { useState, useEffect, useRef } from 'react';
import { Sidebar, SidebarTab } from './components/Sidebar';
import { TopBar, AgentState } from './components/TopBar';
import { ThoughtBox, LogEntry } from './components/ThoughtBox';
import { Dashboard } from './components/Dashboard';
import { ChatInput } from './components/ChatInput';
import { PuterPanel } from './components/PuterPanel';
import { ReasoningBar, ReasoningState } from './components/ReasoningBar';
import { LogPanel } from './components/LogPanel';
import { ReportsPanel } from './components/ReportsPanel';
import { PuterDesktop } from './components/PuterDesktop';

export default function App() {
  const [activeTab, setActiveTab] = useState<SidebarTab>('BROWSER');
  const [agentState, setAgentState] = useState<AgentState>('IDLE');
  const [activeLLM, setActiveLLM] = useState<string>('Groq (llama-3.3-70b)');
  const [currentUrl, setCurrentUrl] = useState<string>('about:blank');
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [puterLogs, setPuterLogs] = useState<any[]>([]);
  const [reasoning, setReasoning] = useState<ReasoningState | null>(null);

  const addLog = (level: LogEntry['level'], message: string) => {
    setLogs(prev => [...prev, {
      id: Math.random().toString(36).substring(7),
      timestamp: new Date().toLocaleTimeString('pt-BR', { hour12: false }),
      level,
      message
    }]);
  };

  const handleClearLogs = () => setLogs([]);
  const handleDownloadLogs = () => {
    const text = logs.map(l => `[${l.timestamp}] ${l.level}: ${l.message}`).join('\n');
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `maestro-logs-${new Date().getTime()}.txt`;
    a.click();
  };

  // Puter.js Integration for Instant Brain
  const askPuter = async (query: string) => {
    const userLog = { id: Math.random().toString(36), message: query, type: 'USER' };
    setPuterLogs(prev => [...prev, userLog]);

    setAgentState('THINKING');
    setReasoning({ thought: 'Puter está analisando a requisição neural...', goal: 'Gerar resposta contextual via Gemini.' });
    addLog('INFO', `[PUTER] Processando consulta neural: ${query.substring(0, 30)}...`);

    try {
      // @ts-ignore
      if (typeof puter === 'undefined') throw new Error('Puter.js não carregado');
      // @ts-ignore
      const response = await puter.ai.chat(query, { model: 'gpt-4o' });
      const messageContent = typeof response === 'string' ? response : (response?.message?.content || 'Sem resposta');

      const aiLog = { id: Math.random().toString(36), message: messageContent, type: 'AI' };
      setPuterLogs(prev => [...prev, aiLog]);
      addLog('INFO', '[PUTER] Resposta processada.');
    } catch (error) {
      addLog('ERROR', `[PUTER] ${error instanceof Error ? error.message : 'Erro na conexão'}`);
    } finally {
      setAgentState('IDLE');
      setReasoning(null);
    }
  };

  // Real Execution via Python Bridge with Streaming
  const executeMacro = async (command: string) => {
    if (agentState !== 'IDLE') return;
    if (command.startsWith('/brain ') || command.startsWith('/ia ')) {
      const query = command.replace(/^\/(brain|ia)\s+/, '');
      await askPuter(query);
      return;
    }

    setActiveTab('BROWSER');
    setAgentState('THINKING');
    addLog('SYSTEM', `[NEURO] Iniciando tarefa: "${command}"`);

    try {
      const response = await fetch('http://localhost:8000/run-agent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command }),
      });

      if (!response.ok) throw new Error('Falha no motor Python');

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) throw new Error('Stream não disponível');

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.substring(6));
            if (data.type === 'step') {
              setAgentState('ACTING');
              setReasoning({ thought: data.thought, goal: data.goal, memory: data.memory });
              if (data.url) setCurrentUrl(data.url);
            } else if (data.type === 'info') {
              addLog('INFO', data.message);
            } else if (data.type === 'done') {
              setAgentState('SYNTHESIZING');
              addLog('INFO', data.message);
              if (data.final_url) setCurrentUrl(data.final_url);
              if (data.summary) addLog('INFO', `RESUMO: ${data.summary}`);
            } else if (data.type === 'error') {
              addLog('ERROR', data.message);
              setAgentState('ERROR');
            }
          }
        }
      }
    } catch (error) {
      addLog('ERROR', `Erro: ${error instanceof Error ? error.message : 'Desconhecido'}`);
      setAgentState('ERROR');
    } finally {
      setTimeout(() => {
        setAgentState('IDLE');
        setReasoning(null);
      }, 2000);
    }
  };

  const handleCopyLogs = () => {
    const logText = logs.map(l => `[${l.timestamp}] ${l.level}: ${l.message}`).join('\n');
    navigator.clipboard.writeText(logText);
    addLog('SYSTEM', 'Logs copiados!');
  };

  const handleSendLogsToAssistant = async () => {
    const logText = logs.map(l => `[${l.timestamp}] ${l.level}: ${l.message}`).join('\n');
    if (!logText) return;
    addLog('SYSTEM', 'Sincronizando logs...');
    try {
      await fetch('http://localhost:8000/save-logs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ logs: logText }),
      });
      addLog('SYSTEM', 'Logs sincronizados com sucesso.');
    } catch (e) {
      addLog('ERROR', 'Falha na sincronização de logs.');
    }
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'DASHBOARD': return <Dashboard />;
      case 'LOGS': return <LogPanel logs={logs} onClear={handleClearLogs} onDownload={handleDownloadLogs} />;
      case 'REPORTS': return <ReportsPanel />;
      case 'PUTER': return <PuterDesktop />;
      case 'BROWSER':
      default:
        return (
          <div className="flex-1 flex gap-4 min-h-0">
            <div className="w-1/2 flex flex-col min-w-[400px]">
              <ThoughtBox logs={logs} />
              <ChatInput onSend={executeMacro} disabled={agentState !== 'IDLE'} />
            </div>
            <div className="flex-1 flex flex-col min-w-[300px]">
              <PuterPanel onPuterAsk={askPuter} isThinking={agentState === 'THINKING'} puterLogs={puterLogs} />
            </div>
          </div>
        );
    }
  };

  return (
    <div className="h-screen w-screen bg-neural-bg text-neural-text flex p-4 overflow-hidden font-sans gap-4">
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        runMacro={executeMacro}
        onCopyLogs={handleCopyLogs}
        onSendLogsToAssistant={handleSendLogsToAssistant}
      />
      <div className="flex-1 flex flex-col min-w-0">
        <TopBar agentState={agentState} activeLLM={activeLLM} currentUrl={currentUrl} />
        <ReasoningBar state={reasoning} isVisible={reasoning !== null} />
        {renderContent()}
      </div>
    </div>
  );
}
