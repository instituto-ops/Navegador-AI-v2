import React from 'react';
import { LayoutDashboard, Globe, MessageSquare, Database, Settings, Play, ShieldAlert, Activity, BarChart3 } from 'lucide-react';

interface SidebarProps {
  activeTab: 'BROWSER' | 'DASHBOARD';
  setActiveTab: (tab: 'BROWSER' | 'DASHBOARD') => void;
  runMacro: (macro: string) => void;
}

export function Sidebar({ activeTab, setActiveTab, runMacro }: SidebarProps) {
  return (
    <div className="w-64 glass-panel h-full flex flex-col p-4 mr-4">
      <div className="flex items-center gap-3 mb-8 px-2">
        <div className="w-8 h-8 rounded-lg bg-neural-accent/20 flex items-center justify-center border border-neural-accent/50">
          <Globe className="w-5 h-5 text-neural-accent" />
        </div>
        <div>
          <h1 className="font-bold tracking-tight text-white">HipnoLawrence</h1>
          <p className="text-[10px] font-mono text-neural-muted uppercase tracking-wider">Agent-First Browser</p>
        </div>
      </div>

      <div className="space-y-6 flex-1">
        <div>
          <h2 className="text-xs font-semibold text-neural-muted uppercase tracking-wider mb-3 px-2">Visão</h2>
          <div className="space-y-1">
            <button
              onClick={() => setActiveTab('BROWSER')}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                activeTab === 'BROWSER' ? 'bg-neural-accent/10 text-neural-accent' : 'text-neural-text hover:bg-white/5'
              }`}
            >
              <Globe className="w-4 h-4" />
              Browser View
            </button>
            <button
              onClick={() => setActiveTab('DASHBOARD')}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                activeTab === 'DASHBOARD' ? 'bg-neural-accent/10 text-neural-accent' : 'text-neural-text hover:bg-white/5'
              }`}
            >
              <LayoutDashboard className="w-4 h-4" />
              Dashboard Unificado
            </button>
          </div>
        </div>

        <div>
          <h2 className="text-xs font-semibold text-neural-muted uppercase tracking-wider mb-3 px-2">Macros Rápidas</h2>
          <div className="space-y-1">
            <button
              onClick={() => runMacro('Auditoria Google Ads')}
              className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm text-neural-text hover:bg-white/5 group transition-colors"
            >
              <div className="flex items-center gap-3">
                <BarChart3 className="w-4 h-4 text-blue-400" />
                Auditar Google Ads
              </div>
              <Play className="w-3 h-3 opacity-0 group-hover:opacity-100 text-neural-accent transition-opacity" />
            </button>
            <button
              onClick={() => runMacro('Scan Doctoralia')}
              className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm text-neural-text hover:bg-white/5 group transition-colors"
            >
              <div className="flex items-center gap-3">
                <Activity className="w-4 h-4 text-yellow-400" />
                Scan Doctoralia
              </div>
              <Play className="w-3 h-3 opacity-0 group-hover:opacity-100 text-neural-accent transition-opacity" />
            </button>
            <button
              onClick={() => runMacro('Verificar WhatsApp')}
              className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm text-neural-text hover:bg-white/5 group transition-colors"
            >
              <div className="flex items-center gap-3">
                <MessageSquare className="w-4 h-4 text-emerald-400" />
                Verificar WhatsApp
              </div>
              <Play className="w-3 h-3 opacity-0 group-hover:opacity-100 text-neural-accent transition-opacity" />
            </button>
          </div>
        </div>

        <div>
          <h2 className="text-xs font-semibold text-neural-muted uppercase tracking-wider mb-3 px-2">Status dos Módulos</h2>
          <div className="space-y-3 px-3">
            <div className="flex items-center justify-between text-xs">
              <span className="text-neural-text">Playwright Core</span>
              <span className="flex items-center gap-1.5 text-neural-accent">
                <span className="w-1.5 h-1.5 rounded-full bg-neural-accent animate-pulse" />
                Online
              </span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-neural-text">Moondream VLM</span>
              <span className="flex items-center gap-1.5 text-neural-accent">
                <span className="w-1.5 h-1.5 rounded-full bg-neural-accent animate-pulse" />
                Online
              </span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-neural-text">Memória RAG</span>
              <span className="flex items-center gap-1.5 text-neural-accent">
                <span className="w-1.5 h-1.5 rounded-full bg-neural-accent animate-pulse" />
                3.2MB
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-auto pt-4 border-t border-neural-border">
        <button className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-neural-text hover:bg-white/5 transition-colors">
          <Settings className="w-4 h-4" />
          Configurações
        </button>
      </div>
    </div>
  );
}
