'use client';

import { useEffect, useState, useRef } from 'react';
import { Terminal } from 'lucide-react';

interface LogStreamProps {
  index: string;
}

export function LogLiveStream({ index }: LogStreamProps) {
  const [logs, setLogs] = useState<{ id: string; line: string }[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const streamUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/logs/stream?index=${index}`;
    const eventSource = new EventSource(streamUrl);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setLogs((prev) => [...prev, data].slice(-50)); // Keep last 50
      } catch (err) {
        console.error('Log stream parse error:', err);
      }
    };

    return () => eventSource.close();
  }, [index]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div className="flex flex-col h-full bg-slate-950 border border-slate-800 rounded-lg overflow-hidden cyber-border">
      <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-900/80 border-b border-slate-800">
        <Terminal className="h-3.5 w-3.5 text-cyan-400" />
        <span className="text-[10px] font-bold text-cyan-400 uppercase tracking-widest">Live Log Feed</span>
        <div className="ml-auto flex gap-1">
          <div className="h-1.5 w-1.5 rounded-full bg-green-500 animate-pulse" />
        </div>
      </div>
      <div 
        ref={scrollRef}
        className="flex-1 p-2 overflow-y-auto font-mono text-[10px] space-y-0.5"
      >
        {logs.length === 0 ? (
          <div className="text-slate-600 italic">Waiting for incoming logs...</div>
        ) : (
          logs.map((log, idx) => (
            <div key={log.id || `log-${idx}`} className="text-slate-300 leading-tight border-l border-slate-800 pl-2">
              <span className="text-cyan-500/70 mr-2">root@siem:~$</span>
              {log.line}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
