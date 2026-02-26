import React from 'react';
import { Globe, Lock, RefreshCw, ChevronLeft, ChevronRight, MousePointer2 } from 'lucide-react';
import { motion } from 'motion/react';
import { AgentState } from './TopBar';

interface BrowserPreviewProps {
  currentUrl: string;
  agentState: AgentState;
  screenshot?: string | null;
}

export function BrowserPreview({ currentUrl, agentState, screenshot }: BrowserPreviewProps) {
  return (
    <div className="glass-panel flex-1 flex flex-col overflow-hidden relative border border-neural-border/50 shadow-2xl min-h-[400px]">
      {/* Browser Chrome */}
      <div className="h-12 bg-[#1a1a1a] border-b border-neural-border flex items-center px-4 gap-4 shrink-0">
        <div className="flex gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500/80" />
          <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
          <div className="w-3 h-3 rounded-full bg-green-500/80" />
        </div>
        
        <div className="flex gap-2 text-neural-muted">
          <ChevronLeft className="w-4 h-4" />
          <ChevronRight className="w-4 h-4 opacity-50" />
          <RefreshCw className={`w-4 h-4 ${agentState === 'ACTING' ? 'animate-spin text-neural-accent' : ''}`} />
        </div>

        <div className="flex-1 bg-black/40 rounded-md h-7 flex items-center px-3 border border-white/5">
          <Lock className="w-3 h-3 text-emerald-500 mr-2" />
          <span className="text-xs font-mono text-neural-text truncate">{currentUrl}</span>
        </div>
      </div>

      {/* Browser Content */}
      <div className="flex-1 bg-white relative overflow-hidden flex flex-col">
        {screenshot ? (
           <img
             src={`data:image/png;base64,${screenshot}`}
             alt="Browser View"
             className="w-full h-full object-contain bg-gray-100"
           />
        ) : (
          /* Simulated/Placeholder Content */
          <>
            {/* Simulated DOM Overlay for OBSERVING state */}
            {agentState === 'OBSERVING' && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="absolute inset-0 bg-blue-500/10 z-10 pointer-events-none"
              >
                <div className="absolute top-1/4 left-1/4 w-32 h-10 border-2 border-blue-500 bg-blue-500/20 flex items-center justify-center">
                  <span className="text-xs font-mono font-bold text-blue-700 bg-white/80 px-1">xpath: //button</span>
                </div>
                <div className="absolute top-1/2 left-1/3 w-64 h-12 border-2 border-blue-500 bg-blue-500/20 flex items-center justify-center">
                  <span className="text-xs font-mono font-bold text-blue-700 bg-white/80 px-1">xpath: //input[@name='q']</span>
                </div>
                {/* Scanline effect */}
                <motion.div
                  animate={{ top: ['0%', '100%', '0%'] }}
                  transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
                  className="absolute left-0 right-0 h-1 bg-blue-400/50 shadow-[0_0_10px_rgba(59,130,246,0.8)]"
                />
              </motion.div>
            )}

            {/* Simulated Mouse for ACTING state */}
            {agentState === 'ACTING' && (
              <motion.div
                initial={{ x: 100, y: 100 }}
                animate={{
                  x: [100, 300, 250, 400],
                  y: [100, 200, 180, 300]
                }}
                transition={{
                  duration: 2,
                  ease: "easeInOut", // Simulating Bezier Curve human mouse
                  times: [0, 0.4, 0.6, 1]
                }}
                className="absolute z-20 pointer-events-none"
              >
                <MousePointer2 className="w-6 h-6 text-black fill-white drop-shadow-md" />
                <motion.div
                  initial={{ scale: 0, opacity: 0 }}
                  animate={{ scale: [0, 1.5, 0], opacity: [0, 1, 0] }}
                  transition={{ delay: 1.8, duration: 0.3 }}
                  className="absolute -top-2 -left-2 w-10 h-10 rounded-full border-2 border-neural-accent"
                />
              </motion.div>
            )}

            {/* Placeholder Content based on URL */}
            <div className="w-full h-full p-8 text-black/80">
              {currentUrl.includes('ads.google.com') ? (
                <div className="space-y-6">
                  <div className="flex items-center justify-between border-b pb-4">
                    <h1 className="text-2xl font-bold text-gray-800">Google Ads | Visão Geral</h1>
                    <div className="w-8 h-8 rounded-full bg-blue-600" />
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="h-24 bg-gray-100 rounded-lg border border-gray-200 p-4">
                      <div className="text-sm text-gray-500 font-medium">Cliques</div>
                      <div className="text-2xl font-bold mt-1">1,245</div>
                    </div>
                    <div className="h-24 bg-gray-100 rounded-lg border border-gray-200 p-4">
                      <div className="text-sm text-gray-500 font-medium">Impressões</div>
                      <div className="text-2xl font-bold mt-1">45.2K</div>
                    </div>
                    <div className="h-24 bg-gray-100 rounded-lg border border-gray-200 p-4">
                      <div className="text-sm text-gray-500 font-medium">Custo</div>
                      <div className="text-2xl font-bold mt-1">R$ 845,20</div>
                    </div>
                  </div>
                </div>
              ) : currentUrl.includes('doctoralia.com.br') ? (
                <div className="space-y-6">
                  <div className="flex items-center gap-4 border-b pb-4">
                    <div className="w-12 h-12 rounded-full bg-emerald-600" />
                    <h1 className="text-2xl font-bold text-gray-800">Doctoralia</h1>
                  </div>
                  <div className="max-w-2xl mx-auto space-y-4">
                     <div className="h-32 bg-white rounded-lg border border-gray-200 shadow-sm p-4 flex gap-4">
                        <div className="w-24 h-24 bg-gray-200 rounded-lg" />
                        <div className="flex-1 space-y-2">
                           <div className="h-6 w-48 bg-gray-200 rounded" />
                           <div className="h-4 w-32 bg-gray-100 rounded" />
                        </div>
                     </div>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center space-y-4">
                    <Globe className="w-16 h-16 text-gray-300 mx-auto" />
                    <h2 className="text-xl font-medium text-gray-500">Navegador Pronto</h2>
                    <p className="text-sm text-gray-400">Aguardando instruções do Maestro.</p>
                  </div>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
