import React, { useState, useEffect, useRef } from 'react';
import { Sidebar } from './components/Sidebar';
import { TopBar, AgentState } from './components/TopBar';
import { ThoughtBox, LogEntry } from './components/ThoughtBox';
import { BrowserPreview } from './components/BrowserPreview';
import { Dashboard } from './components/Dashboard';
import { ChatInput } from './components/ChatInput';

export default function App() {
  const [activeTab, setActiveTab] = useState<'BROWSER' | 'DASHBOARD'>('BROWSER');
  const [agentState, setAgentState] = useState<AgentState>('IDLE');
  const [activeLLM, setActiveLLM] = useState<string>('Groq (llama-3.3-70b)');
  const [currentUrl, setCurrentUrl] = useState<string>('about:blank');
  const [logs, setLogs] = useState<LogEntry[]>([]);

  const addLog = (level: LogEntry['level'], message: string) => {
    setLogs(prev => [...prev, {
      id: Math.random().toString(36).substring(7),
      timestamp: new Date().toLocaleTimeString('pt-BR', { hour12: false }),
      level,
      message
    }]);
  };

  // Simulate the ReAct Loop
  const executeMacro = async (command: string) => {
    if (agentState !== 'IDLE') return;
    
    setActiveTab('BROWSER');
    setAgentState('OBSERVING');
    addLog('SYSTEM', `[MAESTRO] Comando recebido: "${command}"`);
    
    // Step 1: Observing
    await new Promise(r => setTimeout(r, 1000));
    addLog('INFO', 'Injetando DOMObserver e capturando screenshot...');
    await new Promise(r => setTimeout(r, 1500));
    addLog('INFO', 'Extraindo elementos interativos (XPath) com VisionOCR...');
    
    // Step 2: Thinking
    setAgentState('THINKING');
    setActiveLLM('Groq (llama-3.3-70b)');
    addLog('LLM', 'Montando prompt com Identidade LAM + Contexto DOM + RAG...');
    await new Promise(r => setTimeout(r, 2000));
    addLog('LLM', 'Decisão tomada: {"tool": "visual_ads", "args": {"action": "navigate_dashboard"}}');
    
    // Step 3: Acting
    setAgentState('ACTING');
    addLog('INFO', 'Acionando HumanMouse (Bézier cúbico)...');
    if (command.toLowerCase().includes('doctoralia')) {
      setCurrentUrl('https://www.doctoralia.com.br/painel/estatisticas');
    } else {
      setCurrentUrl('https://ads.google.com/aw/overview');
    }
    await new Promise(r => setTimeout(r, 2500));
    addLog('INFO', 'Navegação concluída. Auto-healing verificado.');
    
    // Step 4: Synthesizing
    setAgentState('SYNTHESIZING');
    addLog('INFO', 'Extraindo KPIs do DOM (div[role="row"])...');
    await new Promise(r => setTimeout(r, 1500));
    addLog('SYSTEM', 'Sintetizando relatório estratégico para o Maestro...');
    await new Promise(r => setTimeout(r, 1000));
    
    // Finish
    setAgentState('IDLE');
    addLog('INFO', 'Ciclo ReAct concluído. Aguardando novo comando.');
    if (command.toLowerCase().includes('doctoralia') || command.toLowerCase().includes('ads')) {
      setActiveTab('DASHBOARD');
    }
  };

  return (
    <div className="h-screen w-screen bg-neural-bg text-neural-text flex p-4 overflow-hidden font-sans">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} runMacro={executeMacro} />
      
      <div className="flex-1 flex flex-col min-w-0">
        <TopBar agentState={agentState} activeLLM={activeLLM} currentUrl={currentUrl} />
        
        <div className="flex-1 flex gap-4 min-h-0">
          {/* Left Column: Thought Box & Chat */}
          <div className="w-1/3 flex flex-col min-w-[350px]">
            <ThoughtBox logs={logs} />
            <ChatInput onSend={executeMacro} disabled={agentState !== 'IDLE'} />
          </div>
          
          {/* Right Column: Browser or Dashboard */}
          <div className="flex-1 flex flex-col min-w-0">
            {activeTab === 'BROWSER' ? (
              <BrowserPreview currentUrl={currentUrl} agentState={agentState} />
            ) : (
              <Dashboard />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
