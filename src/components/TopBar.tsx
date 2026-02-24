import React from 'react';
import { Terminal, Activity, Eye, Brain, MousePointerClick, FileText, CheckCircle2, AlertCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

export type AgentState = 'IDLE' | 'OBSERVING' | 'THINKING' | 'ACTING' | 'SYNTHESIZING' | 'ERROR';

interface TopBarProps {
  agentState: AgentState;
  activeLLM: string;
  currentUrl: string;
}

export function TopBar({ agentState, activeLLM, currentUrl }: TopBarProps) {
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

  return (
    <div className="glass-panel h-14 flex items-center justify-between px-6 mb-4">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-neural-accent" />
          <span className="font-mono font-bold tracking-wider text-neural-accent">NEURAL CONSOLE v5.1</span>
        </div>
        <div className="w-px h-6 bg-neural-border mx-2" />
        <div className="flex items-center gap-2">
          <Icon className={`w-4 h-4 ${config.color} ${agentState !== 'IDLE' ? 'animate-pulse' : ''}`} />
          <span className={`text-sm font-medium ${config.color}`}>{config.label}</span>
        </div>
      </div>

      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2 text-sm">
          <span className="text-neural-muted">URL:</span>
          <span className="font-mono text-neural-text bg-black/30 px-2 py-1 rounded border border-neural-border truncate max-w-[300px]">
            {currentUrl}
          </span>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <span className="text-neural-muted">LLM Ativo:</span>
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-neural-accent animate-pulse" />
            <span className="font-mono text-neural-text">{activeLLM}</span>
          </span>
        </div>
      </div>
    </div>
  );
}
