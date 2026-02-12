'use client';

import { useRef, useEffect } from 'react';
import type { ChatResponse } from '@/lib/types';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  response?: ChatResponse;
}

interface ChatMessagesProps {
  messages: ChatMessage[];
  onSelectTab?: (msgId: string, tab: string) => void;
}

export function ChatMessages({ messages }: ChatMessagesProps) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex-1 space-y-4 overflow-y-auto">
      {messages.length === 0 ? (
        <div className="flex h-full items-center justify-center">
          <div className="text-center">
            <div className="text-lg font-semibold text-slate-300">
              No messages yet
            </div>
            <div className="text-sm text-slate-500">
              Start a conversation or run a query
            </div>
          </div>
        </div>
      ) : (
        messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-lg rounded-lg px-4 py-3 ${
                msg.role === 'user'
                  ? 'bg-cyan-600 text-white'
                  : 'border border-slate-700 bg-slate-800 text-slate-100'
              }`}
            >
              <div className="text-sm">{msg.content}</div>
              {msg.response && msg.role === 'assistant' && (
                <div className="mt-2 text-xs text-slate-400">
                  {msg.response.results.totalHits} results found
                </div>
              )}
            </div>
          </div>
        ))
      )}
      <div ref={endRef} />
    </div>
  );
}
