import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts';
import { TrendingUp, Users, Activity, Target, ShieldCheck } from 'lucide-react';

interface DashboardProps {
  authorityLevel?: number;
}

const adsData = [
  { name: 'Seg', clicks: 400, cpa: 24 },
  { name: 'Ter', clicks: 300, cpa: 13 },
  { name: 'Qua', clicks: 200, cpa: 98 },
  { name: 'Qui', clicks: 278, cpa: 39 },
  { name: 'Sex', clicks: 189, cpa: 48 },
  { name: 'Sáb', clicks: 239, cpa: 38 },
  { name: 'Dom', clicks: 349, cpa: 43 },
];

const doctoraliaData = [
  { name: 'Sem 1', rank: 12 },
  { name: 'Sem 2', rank: 10 },
  { name: 'Sem 3', rank: 8 },
  { name: 'Sem 4', rank: 5 },
  { name: 'Sem 5', rank: 3 },
];

export function Dashboard({ authorityLevel = 80 }: DashboardProps) {
  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Dashboard Unificado</h1>
          <p className="text-neural-muted text-sm mt-1">Visão consolidada de Marketing Digital (Ads + Doctoralia)</p>
        </div>
        <div className="flex gap-3">
          <button className="px-4 py-2 rounded-lg bg-neural-accent/10 text-neural-accent border border-neural-accent/20 text-sm font-medium hover:bg-neural-accent/20 transition-colors">
            Exportar Relatório
          </button>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-5 gap-4">
        <div className="glass-panel p-4 relative overflow-hidden">
          <div className="flex items-center justify-between mb-2">
            <span className="text-neural-muted text-sm">Autoridade</span>
            <ShieldCheck className={`w-4 h-4 ${authorityLevel >= 90 ? 'text-emerald-400' : 'text-orange-400'}`} />
          </div>
          <div className="text-2xl font-bold text-white">{authorityLevel}%</div>
          <div className="w-full bg-white/10 h-1 mt-3 rounded-full overflow-hidden">
             <div
               className={`h-full transition-all duration-1000 ${authorityLevel >= 90 ? 'bg-emerald-400' : 'bg-orange-400'}`}
               style={{ width: `${authorityLevel}%` }}
             />
          </div>
          <div className="text-[10px] text-neural-muted mt-2">
            {authorityLevel >= 90 ? 'Navegação Stealth Ativa' : 'Requer Aquecimento'}
          </div>
        </div>

        <div className="glass-panel p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-neural-muted text-sm">CPA Médio (Ads)</span>
            <Target className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-white">R$ 42,50</div>
          <div className="text-xs text-emerald-400 mt-2 flex items-center gap-1">
            <TrendingUp className="w-3 h-3" /> -12% vs mês ant.
          </div>
        </div>
        <div className="glass-panel p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-neural-muted text-sm">Cliques Totais</span>
            <Activity className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-white">1,955</div>
          <div className="text-xs text-emerald-400 mt-2 flex items-center gap-1">
            <TrendingUp className="w-3 h-3" /> +5% vs mês ant.
          </div>
        </div>
        <div className="glass-panel p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-neural-muted text-sm">Ranking Doctoralia</span>
            <Users className="w-4 h-4 text-yellow-400" />
          </div>
          <div className="text-2xl font-bold text-white">3º Lugar</div>
          <div className="text-xs text-emerald-400 mt-2 flex items-center gap-1">
            <TrendingUp className="w-3 h-3" /> Subiu 2 posições
          </div>
        </div>
        <div className="glass-panel p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-neural-muted text-sm">Leads WhatsApp</span>
            <Activity className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold text-white">48</div>
          <div className="text-xs text-neural-muted mt-2 flex items-center gap-1">
            Estável
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-2 gap-6">
        <div className="glass-panel p-6">
          <h3 className="text-sm font-medium text-neural-text mb-6">Desempenho Google Ads (Cliques vs CPA)</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={adsData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                <XAxis dataKey="name" stroke="#888" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#888" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#141414', borderColor: '#333', borderRadius: '8px' }}
                  itemStyle={{ color: '#E0E0E0' }}
                />
                <Bar dataKey="clicks" fill="#00FF9D" radius={[4, 4, 0, 0]} />
                <Bar dataKey="cpa" fill="#3B82F6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="glass-panel p-6">
          <h3 className="text-sm font-medium text-neural-text mb-6">Evolução Ranking Doctoralia</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={doctoraliaData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                <XAxis dataKey="name" stroke="#888" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis reversed stroke="#888" fontSize={12} tickLine={false} axisLine={false} domain={[1, 15]} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#141414', borderColor: '#333', borderRadius: '8px' }}
                  itemStyle={{ color: '#E0E0E0' }}
                />
                <Line type="monotone" dataKey="rank" stroke="#FBBF24" strokeWidth={3} dot={{ r: 6, fill: '#141414', strokeWidth: 2 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
