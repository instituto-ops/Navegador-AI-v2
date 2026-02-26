
import { performance } from 'perf_hooks';

// Mock types
type LogEntry = {
  id: string;
  timestamp: string;
  level: string;
  message: string;
};

// Mock App functions
const runBenchmark = () => {
  // Generate test data
  const lines: string[] = [];
  const iterations = 5000;
  for (let i = 0; i < iterations; i++) {
    lines.push(`data: ${JSON.stringify({ type: 'step', thought: 'thinking...', goal: 'goal', memory: 'mem', elapsed: i, step: i, url: 'http://example.com' })}`);
    lines.push(`data: ${JSON.stringify({ type: 'info', message: 'info message', elapsed: i })}`);
  }

  // --- Unoptimized ---
  let logsState: LogEntry[] = [];
  const setLogsUnopt = (update: any) => {
    if (typeof update === 'function') {
      logsState = update(logsState);
    } else {
      logsState = update;
    }
  };

  const addLogUnopt = (level: string, message: string) => {
    setLogsUnopt((prev: LogEntry[]) => [...prev, {
      id: Math.random().toString(36).substring(7),
      timestamp: new Date().toISOString(),
      level,
      message
    }]);
  };

  const setReasoning = (_: any) => {};
  const setAgentState = (_: any) => {};
  const setCurrentUrl = (_: any) => {};
  const setActiveLLM = (_?: any) => {};

  const startUnopt = performance.now();

  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.substring(6));

      if (data.type === 'step') {
        setAgentState('ACTING');
        setReasoning({
          thought: data.thought,
          goal: data.goal,
          memory: data.memory,
          elapsed: data.elapsed,
          isWaiting: false
        });
        if (data.url) setCurrentUrl(data.url);
        if (data.thought) {
          addLogUnopt('LLM', `[PASSO ${data.step} | ${data.elapsed}s] ${data.thought}`);
        }
      } else if (data.type === 'info') {
        addLogUnopt('INFO', `[${data.elapsed || '...'}s] ${data.message}`);
        if (data.message.includes('Usando') || data.message.includes('Conectando')) {
           // mock logic
           setActiveLLM();
        }
      }
    }
  }

  const endUnopt = performance.now();
  console.log(`Unoptimized time: ${(endUnopt - startUnopt).toFixed(2)}ms`);
  console.log(`Logs count: ${logsState.length}`);


  // --- Optimized ---
  // Reset state
  logsState = [];
  const setLogsOpt = (update: any) => {
      if (typeof update === 'function') {
        logsState = update(logsState);
      } else {
        logsState = update;
      }
  };

  const startOpt = performance.now();

  // Accumulate updates
  let newLogs: LogEntry[] = [];
  let pendingReasoning = null;
  let pendingAgentState = null;
  let pendingUrl = null;
  // let pendingActiveLLM = null; // In real code, we'd track this too

  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.substring(6));

      if (data.type === 'step') {
        pendingAgentState = 'ACTING';
        pendingReasoning = {
          thought: data.thought,
          goal: data.goal,
          memory: data.memory,
          elapsed: data.elapsed,
          isWaiting: false
        };
        if (data.url) pendingUrl = data.url;
        if (data.thought) {
           newLogs.push({
            id: Math.random().toString(36).substring(7),
            timestamp: new Date().toISOString(),
            level: 'LLM',
            message: `[PASSO ${data.step} | ${data.elapsed}s] ${data.thought}`
          });
        }
      } else if (data.type === 'info') {
         newLogs.push({
            id: Math.random().toString(36).substring(7),
            timestamp: new Date().toISOString(),
            level: 'INFO',
            message: `[${data.elapsed || '...'}s] ${data.message}`
          });
          // ... logic for activeLLM would go here
      }
      // ... handle other types
    }
  }

  // Apply updates once
  if (pendingAgentState) setAgentState(pendingAgentState);
  if (pendingReasoning) setReasoning(pendingReasoning);
  if (pendingUrl) setCurrentUrl(pendingUrl);
  if (newLogs.length > 0) {
      setLogsOpt((prev: LogEntry[]) => [...prev, ...newLogs]);
  }

  const endOpt = performance.now();
  console.log(`Optimized time: ${(endOpt - startOpt).toFixed(2)}ms`);
  console.log(`Logs count: ${logsState.length}`);
};

runBenchmark();
