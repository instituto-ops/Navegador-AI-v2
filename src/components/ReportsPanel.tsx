import React, { useState, useEffect } from 'react';
import { FileText, Download, Eye, RefreshCw } from 'lucide-react';

export function ReportsPanel() {
    const [reports, setReports] = useState<string[]>([]);
    const [selectedContent, setSelectedContent] = useState<string | null>(null);
    const [selectedFile, setSelectedFile] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    const fetchReports = async () => {
        setLoading(true);
        try {
            const response = await fetch('http://localhost:8000/reports');
            const data = await response.json();
            setReports(data.reports || []);
        } catch (e) {
            console.error('Falha ao buscar relatórios', e);
        } finally {
            setLoading(false);
        }
    };

    const viewReport = async (filename: string) => {
        try {
            const response = await fetch(`http://localhost:8000/reports/${filename}`);
            const data = await response.json();
            setSelectedContent(data.content);
            setSelectedFile(filename);
        } catch (e) {
            console.error('Falha ao abrir relatório', e);
        }
    };

    useEffect(() => {
        fetchReports();
    }, []);

    return (
        <div className="flex-1 flex gap-4 overflow-hidden h-full">
            {/* List Column */}
            <div className="w-64 glass-panel flex flex-col min-h-0 bg-black/40 border-neural-border">
                <div className="p-4 border-b border-neural-border flex justify-between items-center">
                    <h2 className="text-sm font-bold text-neural-accent flex items-center gap-2">
                        <FileText className="w-4 h-4" />
                        Relatórios
                    </h2>
                    <button onClick={fetchReports} className="text-neural-muted hover:text-neural-accent transition-colors">
                        <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto p-2 space-y-1">
                    {reports.map((report) => (
                        <button
                            key={report}
                            onClick={() => viewReport(report)}
                            className={`w-full text-left p-2 rounded-lg text-xs transition-all flex items-center gap-2 ${selectedFile === report ? 'bg-neural-accent/20 text-neural-accent border border-neural-accent/30' : 'text-neural-text hover:bg-white/5'
                                }`}
                        >
                            <FileText className="w-3 h-3 shrink-0" />
                            <span className="truncate">{report}</span>
                        </button>
                    ))}
                    {reports.length === 0 && !loading && (
                        <div className="text-neural-muted text-[10px] text-center mt-10 p-4">
                            Nenhum relatório gerado ainda.
                        </div>
                    )}
                </div>
            </div>

            {/* Viewer Column */}
            <div className="flex-1 glass-panel bg-black/60 border-neural-border flex flex-col overflow-hidden">
                {selectedContent ? (
                    <>
                        <div className="p-4 border-b border-neural-border flex justify-between items-center bg-black/20">
                            <span className="text-sm font-mono text-neural-accent">{selectedFile}</span>
                            <button className="text-neural-muted hover:text-white flex items-center gap-2 text-xs">
                                <Download className="w-4 h-4" />
                                Baixar
                            </button>
                        </div>
                        <div className="flex-1 overflow-y-auto p-6 font-mono text-sm text-neural-text whitespace-pre-wrap selection:bg-neural-accent/30">
                            {selectedContent}
                        </div>
                    </>
                ) : (
                    <div className="flex-1 flex flex-col items-center justify-center text-neural-muted opacity-50">
                        <Eye className="w-12 h-12 mb-4 animate-pulse" />
                        <p className="text-sm">Selecione um relatório para visualizar o conteúdo</p>
                    </div>
                )}
            </div>
        </div>
    );
}
