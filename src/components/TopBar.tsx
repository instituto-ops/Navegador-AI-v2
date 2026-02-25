import React from 'react';
import { Terminal, Activity, Eye, Brain, MousePointerClick, FileText, CheckCircle2, AlertCircle, Square, Cpu, Zap, Globe, HardDrive } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

export type AgentState = 'IDLE' | 'OBSERVING' | 'THINKING' | 'ACTING' | 'SYNTHESIZING' | 'ERROR';

interface TopBarProps {
  agentState: AgentState;
  activeLLM: string;
  currentUrl: string;
  selectedModel: string;
  onModelChange: (model: string) => void;
  onStop: () => void;
}

export function TopBar({ agentState, activeLLM, currentUrl, selectedModel, onModelChange, onStop }: TopBarProps) {
  const stateConfig = {
    IDLE: { icon: Terminal, color: 'text-neural-muted', label: 'Aguardando Comando' },
    OBSERVING: { icon: Eye, color: 'text-blue-400', label: 'Percepção Visual & DOM' },
    THINKING: { icon: Brain, color: 'text-neural-warning', label: 'Raciocínio ReAct' },
    ACTING: { icon: MousePointerClick, color: 'text-neural-accent', label: 'Executando Ação' },
    SYNTHESIZING: { icon: FileText, color: 'text-purple-400', label: 'Sintetizando Dados' },
    ERROR: { icon: AlertCircle, color: 'text-neural-error', label: 'Falha Crítica' },
  };

  const config = stateConfig[agentState];
  const Icon = config.icon;

  const models = [
    { id: 'auto', label: 'Auto (Cascata)', icon: Zap },
    { id: 'groq', label: 'Groq (Ultra-Rápido)', icon: Cpu },
    { id: 'vision', label: 'Vision / OCR (Coleta Visual)', icon: Eye },
    { id: 'openrouter', label: 'Cloud Master (OR)', icon: Globe },
    { id: 'ollama', label: 'Ollama (Local Privado)', icon: HardDrive },
  ];

  return (
    <div className="glass-panel h-14 flex items-center justify-between px-6 mb-4">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-neural-accent" />
          <span className="font-mono font-bold tracking-wider text-neural-accent">MAESTRO OS v5.2</span>
        </div>
        <div className="w-px h-6 bg-neural-border mx-2" />
        <div className="flex items-center gap-2">
          <Icon className={`w-4 h-4 ${config.color} ${agentState !== 'IDLE' ? 'animate-pulse' : ''}`} />
          <span className={`text-sm font-medium ${config.color} uppercase tracking-tighter`}>{config.label}</span>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {/* Model Selector */}
        <div className="flex bg-black/40 border border-neural-border p-0.5 rounded-lg">
          {models.map((m) => {
            const MIcon = m.icon;
            const active = selectedModel === m.id;
            return (
              <button
                key={m.id}
                onClick={() => onModelChange(m.id)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-[10px] font-bold uppercase transition-all ${active
                  ? 'bg-neural-accent text-black'
                  : 'text-neural-muted hover:text-neural-text'
                  }`}
                title={m.label}
              >
                <MIcon className="w-3 h-3" />
                <span className="hidden xl:inline">{m.id}</span>
              </button>
            );
          })}
        </div>

        {/* URL Display */}
        <div className="flex items-center gap-2 text-[10px] bg-black/30 border border-neural-border px-3 py-1.5 rounded-lg font-mono">
          <span className="text-neural-muted uppercase">URL:</span>
          <span className="text-neural-text truncate max-w-[200px]">{currentUrl}</span>
        </div>

        {/* Stop Button */}
        <AnimatePresence>
          {agentState !== 'IDLE' && (
            <motion.button
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              onClick={onStop}
              className="flex items-center gap-2 bg-neural-error/20 hover:bg-neural-error text-neural-error hover:text-white border border-neural-error/50 px-4 py-1.5 rounded-lg text-[10px] font-bold uppercase transition-all"
            >
              <Square className="w-3 h-3 fill-current" />
              Parar
            </motion.button>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
