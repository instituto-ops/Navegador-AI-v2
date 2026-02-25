import React from 'react';
import { Monitor, Maximize2, ExternalLink } from 'lucide-react';

export function PuterDesktop() {
    return (
        <div className="glass-panel flex-1 flex flex-col overflow-hidden bg-black/40 border-neural-border">
            <div className="h-12 border-b border-neural-border flex items-center justify-between px-6 bg-black/20">
                <div className="flex items-center gap-3">
                    <Monitor className="w-5 h-5 text-neural-accent" />
                    <h2 className="text-sm font-bold uppercase tracking-widest text-neural-text">Puter Virtual OS</h2>
                </div>
                <div className="flex items-center gap-4 text-xs text-neural-muted">
                    <a href="https://puter.com" target="_blank" rel="noopener noreferrer" className="hover:text-neural-accent flex items-center gap-1">
                        Open Web Version <ExternalLink className="w-3 h-3" />
                    </a>
                </div>
            </div>

            <div className="flex-1 bg-black relative group">
                <iframe
                    src="https://puter.com/app/desktop"
                    className="w-full h-full border-none"
                    title="Puter Desktop"
                    allow="autoplay; camera; microphone; fullscreen; geolocation;"
                />

                {/* Connection Overlay */}
                <div className="absolute top-4 right-4 bg-neural-accent/90 text-black px-3 py-1 rounded-full text-[10px] font-bold flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <div className="w-1.5 h-1.5 rounded-full bg-black animate-pulse" />
                    PONTE NEURAL ATIVA
                </div>

                <div className="absolute bottom-10 left-1/2 -translate-x-1/2 bg-black/90 border border-neural-border p-6 rounded-2xl text-center max-w-sm opacity-0 group-hover:opacity-100 transition-all transform translate-y-4 group-hover:translate-y-0 backdrop-blur-md">
                    <Monitor className="w-8 h-8 text-neural-accent mx-auto mb-3" />
                    <p className="text-xs text-neural-text mb-4">Se o desktop não carregar, use o botão de acesso direto abaixo.</p>
                    <a
                        href="https://puter.com"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="bg-neural-accent text-black px-4 py-2 rounded-lg text-[10px] font-bold hover:scale-105 transition-transform inline-block"
                    >
                        ABRIR ESTAÇÃO EXTERNA
                    </a>
                </div>
            </div>
        </div>
    );
}
