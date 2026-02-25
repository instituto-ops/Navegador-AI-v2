import React, { useState, useEffect, useRef } from 'react';
import { Brain, Cpu, Zap, Activity, Send, Terminal } from 'lucide-react';

interface PuterLog {
    id: string;
    message: string;
    type: 'USER' | 'AI' | 'SYSTEM';
}

interface PuterPanelProps {
    onPuterAsk: (query: string) => void;
    isThinking: boolean;
    puterLogs: PuterLog[];
}

export function PuterPanel({ onPuterAsk, isThinking, puterLogs }: PuterPanelProps) {
    const [input, setInput] = useState('');
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [puterLogs]);

    const handleSend = (e: React.FormEvent) => {
        e.preventDefault();
        if (input.trim() && !isThinking) {
            onPuterAsk(input.trim());
            setInput('');
        }
    };

    return (
        <div className="flex-1 flex flex-col min-w-0 glass-panel overflow-hidden border-l border-neural-border/30 font-sans shadow-2xl">
            {/* Header */}
            <div className="p-4 border-b border-neural-border/30 flex items-center justify-between bg-black/40">
                <div className="flex items-center gap-2">
                    <Brain className="w-5 h-5 text-neural-accent" />
                    <h2 className="font-semibold text-neural-text uppercase tracking-wider text-xs">Cérebro Auxiliar (Puter)</h2>
                </div>
                <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${isThinking ? 'bg-neural-accent animate-ping' : 'bg-green-500'}`}></span>
                    <span className="text-[10px] text-neural-muted font-mono">{isThinking ? 'LENDO...' : 'PRONTO'}</span>
                </div>
            </div>

            {/* Response Area (Dedicated for Puter) */}
            <div
                ref={scrollRef}
                className="flex-1 p-4 overflow-y-auto space-y-4 bg-black/20 font-mono text-[11px]"
            >
                {puterLogs.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-neural-muted opacity-40 gap-3">
                        <Terminal className="w-12 h-12" />
                        <p className="text-center italic px-8">Aguardando gatilho neural... Esta área é exclusiva para respostas do Puter.js</p>
                    </div>
                ) : (
                    puterLogs.map((log) => (
                        <div key={log.id} className={`flex flex-col ${log.type === 'USER' ? 'items-end' : 'items-start'}`}>
                            <div className={`max-w-[90%] rounded-lg p-3 ${log.type === 'USER'
                                ? 'bg-neural-accent/10 border border-neural-accent/20 text-neural-accent'
                                : log.type === 'SYSTEM'
                                    ? 'bg-white/5 text-neural-muted italic'
                                    : 'bg-white/5 border border-white/10 text-neural-text'
                                }`}>
                                {log.type === 'AI' && <div className="text-[9px] text-neural-accent font-bold mb-1 uppercase tracking-tighter">Puter Engine //</div>}
                                <div className="whitespace-pre-wrap">
                                    {typeof log.message === 'string' ? log.message : JSON.stringify(log.message)}
                                </div>
                            </div>
                        </div>
                    ))
                )}
                {isThinking && (
                    <div className="flex gap-2 items-center text-neural-accent animate-pulse">
                        <span className="w-1.5 h-1.5 bg-neural-accent rounded-full"></span>
                        <span>Processando impulsos...</span>
                    </div>
                )}
            </div>

            {/* Status Bar */}
            <div className="px-4 py-2 bg-black/40 border-t border-neural-border/10 flex justify-between items-center text-[10px] text-neural-muted">
                <div className="flex gap-4">
                    <span>MODEL: GEMINI PRO</span>
                    <span>TOKEN: FREE</span>
                </div>
                <Activity className="w-3 h-3 text-neural-accent/50" />
            </div>

            {/* Dedicated Puter Chat Input */}
            <div className="p-4 bg-black/60 border-t border-neural-border/30">
                <form onSubmit={handleSend} className="relative">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        disabled={isThinking}
                        placeholder="Comando Cerebral..."
                        className="w-full bg-black/40 border border-neural-border/50 rounded-lg py-3 pl-4 pr-12 text-xs text-white focus:outline-none focus:border-neural-accent transition-all placeholder:text-neural-muted/50"
                    />
                    <button
                        type="submit"
                        disabled={isThinking || !input.trim()}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-neural-accent hover:text-white transition-all disabled:opacity-30 disabled:grayscale"
                    >
                        <Send className="w-4 h-4" />
                    </button>
                </form>
            </div>
        </div>
    );
}
