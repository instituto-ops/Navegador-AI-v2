import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import App from './App';

// Mock child components to isolate App logic
vi.mock('./components/Dashboard', () => ({
  Dashboard: () => <div data-testid="dashboard">Dashboard Component</div>
}));
vi.mock('./components/BrowserPreview', () => ({
  BrowserPreview: () => <div data-testid="browser-preview">BrowserPreview Component</div>
}));
vi.mock('./components/LogPanel', () => ({
  LogPanel: () => <div data-testid="log-panel">LogPanel Component</div>
}));
vi.mock('./components/ReportsPanel', () => ({
  ReportsPanel: () => <div data-testid="reports-panel">ReportsPanel Component</div>
}));
vi.mock('./components/PuterDesktop', () => ({
  PuterDesktop: () => <div data-testid="puter-desktop">PuterDesktop Component</div>
}));
vi.mock('./components/ThoughtBox', () => ({
  ThoughtBox: ({ logs }: { logs: any[] }) => (
    <div data-testid="thought-box">
      {logs.map((log) => (
        <div key={log.id}>{log.message}</div>
      ))}
    </div>
  )
}));

// Mock Lucide icons
vi.mock('lucide-react', () => ({
  LayoutDashboard: () => <span data-testid="icon-dashboard" />,
  Globe: () => <span data-testid="icon-globe" />,
  MessageSquare: () => <span data-testid="icon-message" />,
  Database: () => <span data-testid="icon-database" />,
  Settings: () => <span data-testid="icon-settings" />,
  Play: () => <span data-testid="icon-play" />,
  ShieldAlert: () => <span data-testid="icon-shield" />,
  Activity: () => <span data-testid="icon-activity" />,
  BarChart3: () => <span data-testid="icon-barchart" />,
  Terminal: () => <span data-testid="icon-terminal" />,
  FileText: () => <span data-testid="icon-filetext" />,
  Monitor: () => <span data-testid="icon-monitor" />,
  Zap: () => <span data-testid="icon-zap" />,
  Brain: () => <span data-testid="icon-brain" />,
  MousePointer2: () => <span data-testid="icon-mouse" />,
  AlertCircle: () => <span data-testid="icon-alert" />,
  Cpu: () => <span data-testid="icon-cpu" />,
  HardDrive: () => <span data-testid="icon-harddrive" />,
  Square: () => <span data-testid="icon-square" />,
  Eye: () => <span data-testid="icon-eye" />,
  ExternalLink: () => <span data-testid="icon-external" />,
  Send: () => <span data-testid="icon-send" />,
  Command: () => <span data-testid="icon-command" />,
  Search: () => <span data-testid="icon-search" />,
  Clock: () => <span data-testid="icon-clock" />,
  Target: () => <span data-testid="icon-target" />,
  Loader2: () => <span data-testid="icon-loader2" />,
}));

// Mock motion/react
vi.mock('motion/react', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    button: ({ children, ...props }: any) => <button {...props}>{children}</button>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

// Mock global fetch
const fetchMock = vi.fn();
global.fetch = fetchMock;

// Mock puter global
(global as any).puter = {
  ai: {
    chat: vi.fn()
  }
};

// Mock ScrollIntoView
Element.prototype.scrollIntoView = vi.fn();

describe('App Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders correctly', () => {
    render(<App />);
    expect(screen.getByText('Maestro OS')).toBeInTheDocument();
    expect(screen.getByTestId('browser-preview')).toBeInTheDocument();
  });

  it('navigates between tabs', async () => {
    const user = userEvent.setup();
    render(<App />);

    // Initial state: Browser
    expect(screen.getByTestId('browser-preview')).toBeInTheDocument();

    // Click Dashboard
    const dashboardBtn = screen.getByText('Dashboard');
    await user.click(dashboardBtn);
    expect(screen.getByTestId('dashboard')).toBeInTheDocument();
    expect(screen.queryByTestId('browser-preview')).not.toBeInTheDocument();

    // Click Logs
    const logsBtn = screen.getByText('Audit Logs');
    await user.click(logsBtn);
    expect(screen.getByTestId('log-panel')).toBeInTheDocument();
  });

  it('executes a macro', async () => {
    const user = userEvent.setup();

    // Mock streaming response
    const stream = new ReadableStream({
      start(controller) {
        const encoder = new TextEncoder();
        const data = JSON.stringify({
          type: 'info',
          message: 'Executing command...',
          elapsed: 0.1
        });
        const chunk = `data: ${data}\n\n`;
        controller.enqueue(encoder.encode(chunk));
        controller.close();
      }
    });

    const response = new Response(stream, {
        headers: { 'Content-Type': 'text/event-stream' }
    });

    fetchMock.mockResolvedValueOnce(response);

    render(<App />);

    const input = screen.getByPlaceholderText(/Commando para o Maestro/i);
    await user.type(input, 'Test Command');

    const sendBtn = screen.getByText('Enviar');
    await user.click(sendBtn);

    expect(fetchMock).toHaveBeenCalledWith('http://localhost:8000/run-agent', expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({ command: 'Test Command', model: 'auto' }),
    }));

    // Wait for the log to appear
    await waitFor(() => {
      expect(screen.getByText(/Executing command/i)).toBeInTheDocument();
    });
  });
});
