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
                    src="https://puter.com"
                    className="w-full h-full border-none"
                    title="Puter Desktop"
                    allow="autoplay; camera; microphone; fullscreen; geolocation;"
                />

                {/* Connection Overlay */}
                <div className="absolute top-4 right-4 bg-neural-accent/90 text-black px-3 py-1 rounded-full text-[10px] font-bold flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <div className="w-1.5 h-1.5 rounded-full bg-black animate-pulse" />
                    LIVE BRIDGE ACTIVE
                </div>
            </div>
        </div>
    );
}
