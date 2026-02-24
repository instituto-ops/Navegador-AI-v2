import React, { useState } from 'react';
import { Send, Command } from 'lucide-react';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [input, setInput] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput('');
    }
  };

  return (
    <div className="glass-panel p-4 mt-4 shrink-0">
      <form onSubmit={handleSubmit} className="flex gap-3">
        <div className="flex-1 relative">
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-neural-muted">
            <Command className="w-4 h-4" />
          </div>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={disabled}
            placeholder={disabled ? "Agente em execução..." : "Comando para o Maestro (ex: 'Analise as campanhas do Google Ads')"}
            className="w-full bg-black/40 border border-neural-border rounded-lg py-3 pl-10 pr-4 text-sm text-white placeholder:text-neural-muted focus:outline-none focus:border-neural-accent/50 focus:ring-1 focus:ring-neural-accent/50 transition-all disabled:opacity-50"
          />
        </div>
        <button
          type="submit"
          disabled={disabled || !input.trim()}
          className="bg-neural-accent text-black px-6 rounded-lg font-medium flex items-center gap-2 hover:bg-neural-accent/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span>Enviar</span>
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}
