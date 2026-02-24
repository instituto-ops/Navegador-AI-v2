import React, { useEffect, useRef } from 'react';
import { Terminal } from 'lucide-react';

export interface LogEntry {
  id: string;
  timestamp: string;
  level: 'INFO' | 'WARN' | 'ERROR' | 'SYSTEM' | 'LLM';
  message: string;
}

interface ThoughtBoxProps {
  logs: LogEntry[];
}

export function ThoughtBox({ logs }: ThoughtBoxProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  const getLogColor = (level: string) => {
    switch (level) {
      case 'INFO': return 'text-blue-400';
      case 'WARN': return 'text-neural-warning';
      case 'ERROR': return 'text-neural-error';
      case 'SYSTEM': return 'text-neural-accent';
      case 'LLM': return 'text-purple-400';
      default: return 'text-neural-text';
    }
  };

  return (
    <div className="glass-panel flex-1 flex flex-col overflow-hidden relative">
      <div className="h-10 border-b border-neural-border flex items-center px-4 bg-black/20">
        <Terminal className="w-4 h-4 text-neural-muted mr-2" />
        <span className="text-xs font-mono font-semibold tracking-wider text-neural-muted uppercase">Thought Box (ReAct Loop)</span>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 scanline" ref={scrollRef}>
        <div className="space-y-1.5">
          {logs.map((log) => (
            <div key={log.id} className="terminal-text flex gap-3">
              <span className="text-neural-muted opacity-50 shrink-0">[{log.timestamp}]</span>
              <span className={`${getLogColor(log.level)} font-bold shrink-0 w-16`}>{log.level}</span>
              <span className="text-neural-text break-words">{log.message}</span>
            </div>
          ))}
          {logs.length === 0 && (
            <div className="terminal-text text-neural-muted italic">Aguardando inicialização do motor cognitivo...</div>
          )}
        </div>
      </div>
    </div>
  );
}
