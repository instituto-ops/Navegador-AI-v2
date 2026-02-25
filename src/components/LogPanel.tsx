import React, { useEffect, useRef } from 'react';
import { Terminal, Trash2, Download } from 'lucide-react';
import { LogEntry } from './ThoughtBox';

interface LogPanelProps {
    logs: LogEntry[];
    onClear: () => void;
    onDownload: () => void;
}

export function LogPanel({ logs, onClear, onDownload }: LogPanelProps) {
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
        <div className="glass-panel flex-1 flex flex-col overflow-hidden bg-black/60 border-neural-border">
            <div className="h-12 border-b border-neural-border flex items-center justify-between px-6 bg-black/40">
                <div className="flex items-center gap-3">
                    <Terminal className="w-5 h-5 text-neural-accent" />
                    <h2 className="text-sm font-bold uppercase tracking-widest text-neural-text">Neural Stream Console</h2>
                </div>
                <div className="flex items-center gap-4">
                    <button onClick={onDownload} className="text-neural-muted hover:text-white transition-colors flex items-center gap-2 text-xs">
                        <Download className="w-4 h-4" />
                        Exportar
                    </button>
                    <button onClick={onClear} className="text-neural-muted hover:text-neural-error transition-colors flex items-center gap-2 text-xs">
                        <Trash2 className="w-4 h-4" />
                        Limpar
                    </button>
                </div>
            </div>

            <div className="flex-1 overflow-y-auto p-6 font-mono text-[13px] leading-relaxed scanline" ref={scrollRef}>
                <div className="space-y-1">
                    {logs.map((log) => (
                        <div key={log.id} className="flex gap-4 group hover:bg-white/5 p-1 rounded transition-colors">
                            <span className="text-neural-muted opacity-40 shrink-0 select-none">[{log.timestamp}]</span>
                            <span className={`${getLogColor(log.level)} font-bold shrink-0 w-16 text-center border border-current/20 rounded text-[10px] py-0.5`}>
                                {log.level}
                            </span>
                            <span className="text-neural-text break-words opacity-90 group-hover:opacity-100">{log.message}</span>
                        </div>
                    ))}
                    {logs.length === 0 && (
                        <div className="h-full flex items-center justify-center text-neural-muted italic opacity-50">
                            Terminal ocioso. Aguardando atividade da rede neural...
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
