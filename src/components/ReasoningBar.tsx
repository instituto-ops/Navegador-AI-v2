import React from 'react';
import { Brain, Target, Zap, MessageSquare } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

export interface ReasoningState {
    thought?: string;
    goal?: string;
    memory?: string;
    lastAction?: string;
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
            className="glass-panel mb-4 overflow-hidden border-neural-accent/20 bg-neural-accent/5"
        >
            <div className="p-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {/* Thought Block */}
                <div className="flex gap-3">
                    <div className="shrink-0 p-2 rounded-lg bg-neural-accent/10 h-fit">
                        <Brain className="w-4 h-4 text-neural-accent" />
                    </div>
                    <div className="flex-1 min-w-0">
                        <div className="text-[10px] text-neural-muted uppercase tracking-tighter mb-1 font-bold">Processamento Cognitivo</div>
                        <p className="text-xs text-neural-text leading-relaxed italic line-clamp-3">
                            "{state.thought || 'Analisando ambiente digital...'}"
                        </p>
                    </div>
                </div>

                {/* Goal Block */}
                <div className="flex gap-3">
                    <div className="shrink-0 p-2 rounded-lg bg-blue-500/10 h-fit">
                        <Target className="w-4 h-4 text-blue-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                        <div className="text-[10px] text-blue-400 uppercase tracking-tighter mb-1 font-bold">Próximo Objetivo Neural</div>
                        <p className="text-xs text-neural-text leading-relaxed font-mono truncate">
                            {state.goal || 'Definindo próximo passo...'}
                        </p>
                    </div>
                </div>

                {/* Memory/Action Block */}
                <div className="flex gap-3 lg:col-span-1 md:col-span-2">
                    <div className="shrink-0 p-2 rounded-lg bg-purple-500/10 h-fit">
                        <Zap className="w-4 h-4 text-purple-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                        <div className="text-[10px] text-purple-400 uppercase tracking-tighter mb-1 font-bold">Estado da Memória Externa</div>
                        <p className="text-xs text-neural-muted leading-relaxed truncate">
                            {state.memory || 'Sincronizando cache de curto prazo...'}
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
