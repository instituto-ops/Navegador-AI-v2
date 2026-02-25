import React from 'react';
import {
  LayoutDashboard,
  Globe,
  MessageSquare,
  Database,
  Settings,
  Play,
  ShieldAlert,
  Activity,
  BarChart3,
  Terminal,
  FileText,
  Monitor,
  Zap,
  Brain
} from 'lucide-react';

export type SidebarTab = 'BROWSER' | 'DASHBOARD' | 'LOGS' | 'REPORTS' | 'PUTER';

interface SidebarProps {
  activeTab: SidebarTab;
  setActiveTab: (tab: SidebarTab) => void;
  runMacro: (macro: string) => void;
  onCopyLogs: () => void;
  onSendLogsToAssistant: () => void;
}

export function Sidebar({ activeTab, setActiveTab, runMacro, onCopyLogs, onSendLogsToAssistant }: SidebarProps) {
  const menuItems = [
    { id: 'BROWSER', icon: Globe, label: 'Navegador AI', color: 'text-blue-400' },
    { id: 'DASHBOARD', icon: LayoutDashboard, label: 'Dashboard', color: 'text-purple-400' },
    { id: 'LOGS', icon: Terminal, label: 'Audit Logs', color: 'text-neural-accent' },
    { id: 'REPORTS', icon: FileText, label: 'Reports', color: 'text-emerald-400' },
    { id: 'PUTER', icon: Monitor, label: 'Puter Virtual', color: 'text-orange-400' },
  ] as const;

  return (
    <div className="w-64 glass-panel h-full flex flex-col p-4 mr-4">
      <div className="flex items-center gap-3 mb-8 px-2">
        <div className="w-8 h-8 rounded-lg bg-neural-accent/20 flex items-center justify-center border border-neural-accent/50">
          <Brain className="w-5 h-5 text-neural-accent" />
        </div>
        <div>
          <h1 className="font-bold tracking-tight text-white">Maestro OS</h1>
          <p className="text-[10px] font-mono text-neural-muted uppercase tracking-wider">Neural Assistant v5.1</p>
        </div>
      </div>

      <div className="space-y-6 flex-1 overflow-y-auto pr-2 custom-scrollbar">
        <div>
          <h2 className="text-xs font-semibold text-neural-muted uppercase tracking-wider mb-3 px-2">Sistemas Core</h2>
          <div className="space-y-1">
            {menuItems.map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id as SidebarTab)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 ${activeTab === item.id
                    ? 'bg-neural-accent text-black font-bold shadow-lg shadow-neural-accent/20'
                    : 'text-neural-text hover:bg-white/5'
                  }`}
              >
                <item.icon className={`w-4 h-4 ${activeTab === item.id ? 'text-black' : item.color}`} />
                {item.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <h2 className="text-xs font-semibold text-neural-muted uppercase tracking-wider mb-3 px-2">Macros Rápidas</h2>
          <div className="space-y-1">
            <button
              onClick={() => runMacro('Análise de Mercado')}
              className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm text-neural-text hover:bg-white/5 group transition-colors"
            >
              <div className="flex items-center gap-3">
                <BarChart3 className="w-4 h-4 text-blue-400" />
                Auditar Web
              </div>
              <Play className="w-3 h-3 opacity-0 group-hover:opacity-100 text-neural-accent transition-opacity" />
            </button>
            <button
              onClick={() => runMacro('Limpar Cache Neural')}
              className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm text-neural-text hover:bg-white/5 group transition-colors"
            >
              <div className="flex items-center gap-3">
                <Zap className="w-4 h-4 text-yellow-400" />
                Limpar Cache
              </div>
              <Play className="w-3 h-3 opacity-0 group-hover:opacity-100 text-neural-accent transition-opacity" />
            </button>
          </div>
        </div>

        <div>
          <h2 className="text-xs font-semibold text-neural-muted uppercase tracking-wider mb-3 px-2">Log Center</h2>
          <div className="space-y-2 px-2">
            <button
              onClick={onCopyLogs}
              className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-[11px] bg-white/5 text-neural-text hover:bg-neural-accent/10 hover:text-neural-accent transition-all border border-white/5"
            >
              <Database className="w-3.5 h-3.5" />
              Copiar Logs Sessão
            </button>
            <button
              onClick={onSendLogsToAssistant}
              className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-[11px] bg-neural-accent/5 text-neural-accent hover:bg-neural-accent/20 transition-all border border-neural-accent/20"
            >
              <ShieldAlert className="w-3.5 h-3.5" />
              Enviar Logs para Antigravity
            </button>
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
