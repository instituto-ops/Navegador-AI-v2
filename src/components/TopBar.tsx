import React from 'react';
import { Activity, Brain, MousePointer2, AlertCircle, Zap, Cpu, Globe, HardDrive, Square, Eye, ExternalLink } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

export type AgentState = 'IDLE' | 'THINKING' | 'ACTING' | 'ERROR' | 'OBSERVING';

interface TopBarProps {
  agentState: AgentState;
  activeLLM: string;
  currentUrl: string;
  selectedModel: string;
  onModelChange: (model: string) => void;
  onStop: () => void;
  onOpenBrowser: () => void;
}

export function TopBar({ agentState, activeLLM, currentUrl, selectedModel, onModelChange, onStop, onOpenBrowser }: TopBarProps) {
  const stateConfig = {
    IDLE: { label: 'Ocioso', color: 'text-neural-muted', icon: Activity },
    THINKING: { label: 'Processando', color: 'text-neural-accent animate-pulse', icon: Brain },
    ACTING: { label: 'Agindo', color: 'text-neural-success', icon: MousePointer2 },
    ERROR: { label: 'Falha Crítica', color: 'text-neural-error', icon: AlertCircle },
    OBSERVING: { label: 'Observando', color: 'text-blue-400', icon: Eye },
  };

  const models = [
    { id: 'auto', label: 'Auto (Cascata)', icon: Zap },
    { id: 'groq', label: 'Groq (Ultra-Rápido)', icon: Cpu },
    { id: 'vision', label: 'Vision / OCR (Coleta Visual)', icon: Eye },
    { id: 'smol', label: 'Smol (Local Ultra-Leve)', icon: Zap },
    { id: 'openrouter', label: 'Cloud Master (OR)', icon: Globe },
    { id: 'ollama', label: 'Ollama (Local Privado)', icon: HardDrive },
  ];

  const config = stateConfig[agentState];
  const Icon = config.icon;

  return (
    <div className="glass-panel h-14 flex items-center justify-between px-6 mb-4">
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-3 pr-6 border-r border-neural-border/50">
          <div className={`p-1.5 rounded-md bg-black/20 ${config.color}`}>
            <Icon className="w-4 h-4" />
          </div>
          <div>
            <div className="text-[10px] text-neural-muted uppercase tracking-tighter font-bold">Status do Núcleo</div>
            <div className={`text-xs font-mono font-bold leading-none ${config.color}`}>
              {config.label}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="p-1.5 rounded-md bg-neural-accent/10">
            <Cpu className="w-4 h-4 text-neural-accent" />
          </div>
          <div>
            <div className="text-[10px] text-neural-muted uppercase tracking-tighter font-bold">Neural Engine</div>
            <div className="text-xs font-mono text-neural-text font-bold leading-none">{activeLLM}</div>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {/* Abrir Navegador Button */}
        <button
          onClick={onOpenBrowser}
          className="flex items-center gap-2 bg-neural-accent/10 hover:bg-neural-accent/20 text-neural-accent border border-neural-accent/30 px-4 py-1.5 rounded-lg text-[10px] font-bold uppercase transition-all"
        >
          <ExternalLink className="w-3 h-3" />
          Instância Navegador
        </button>

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
