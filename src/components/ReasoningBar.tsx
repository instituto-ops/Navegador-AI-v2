import React from 'react';
import { Brain, Target, Zap, Clock, Loader2, Search } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

export interface ReasoningState {
    thought?: string;
    goal?: string;
    memory?: string;
    lastAction?: string;
    elapsed?: number;
    isWaiting?: boolean;
}

interface ReasoningBarProps {
    state: ReasoningState | null;
    isVisible: boolean;
}

export function ReasoningBar({ state, isVisible }: ReasoningBarProps) {
    if (!isVisible || !state) return null;

    return (
        <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="glass-panel mb-4 overflow-hidden border-neural-accent/20 bg-neural-accent/5 backdrop-blur-xl"
        >
            <div className="p-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Status/Time Block */}
                <div className="flex gap-3">
                    <div className="shrink-0 p-2 rounded-lg bg-neural-accent/10 h-fit">
                        {state.isWaiting ? (
                            <Search className="w-4 h-4 text-neural-accent animate-spin" />
                        ) : (
                            <Clock className="w-4 h-4 text-neural-accent" />
                        )}
                    </div>
                    <div className="flex-1 min-w-0">
                        <div className="text-[10px] text-neural-muted uppercase tracking-tighter mb-1 font-bold">Monitor de Latência</div>
                        <div className="flex items-center gap-2">
                            <span className="text-xs font-mono text-neural-text">
                                {state.isWaiting ? 'Aguardando Servidor...' : `${state.elapsed || 0}s Decorridos`}
                            </span>
                        </div>
                    </div>
                </div>

                {/* Thought Block */}
                <div className="flex gap-3">
                    <div className="shrink-0 p-2 rounded-lg bg-blue-500/10 h-fit">
                        <Brain className="w-4 h-4 text-blue-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                        <div className="text-[10px] text-blue-400 uppercase tracking-tighter mb-1 font-bold">Processamento Cognitivo</div>
                        <p className="text-xs text-neural-text leading-relaxed italic line-clamp-2">
                            "{state.thought || 'Analisando ambiente digital...'}"
                        </p>
                    </div>
                </div>

                {/* Goal Block */}
                <div className="flex gap-3">
                    <div className="shrink-0 p-2 rounded-lg bg-neural-warning/10 h-fit">
                        <Target className="w-4 h-4 text-neural-warning" />
                    </div>
                    <div className="flex-1 min-w-0">
                        <div className="text-[10px] text-neural-warning uppercase tracking-tighter mb-1 font-bold">Objetivo Neural</div>
                        <p className="text-xs text-neural-text leading-relaxed font-mono truncate">
                            {state.goal || 'Definindo próximo passo...'}
                        </p>
                    </div>
                </div>

                {/* Memory/Action Block */}
                <div className="flex gap-3">
                    <div className="shrink-0 p-2 rounded-lg bg-purple-500/10 h-fit">
                        <Zap className="w-4 h-4 text-purple-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                        <div className="text-[10px] text-purple-400 uppercase tracking-tighter mb-1 font-bold">Memória Externa</div>
                        <p className="text-xs text-neural-muted leading-relaxed truncate">
                            {state.memory || 'Sincronizando cache...'}
                        </p>
                    </div>
                </div>
            </div>

            {/* Visual Activity Indicator */}
            <div className="h-0.5 bg-neural-border relative overflow-hidden">
                <motion.div
                    className="absolute inset-y-0 bg-neural-accent"
                    animate={{
                        x: ['-100%', '200%'],
                    }}
                    transition={{
                        duration: 2,
                        repeat: Infinity,
                        ease: "easeInOut"
                    }}
                    style={{ width: '30%' }}
                />
            </div>
        </motion.div>
    );
}
