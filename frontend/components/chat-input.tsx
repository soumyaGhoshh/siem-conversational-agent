'use client';

import React from "react"

import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

interface ChatInputProps {
  onSubmit: (message: string) => void;
  isLoading?: boolean;
  prefilledQuery?: string;
}

const PRESET_CHIPS = [
  'Show critical alerts (level > 12) in last 24h',
  'Identify top source IPs for failed logins',
  'Summarize potential attack stories',
  'Find anomalous file deletions',
  'Check for privilege escalation attempts',
  'List top 10 most active agents',
  'Detect RDP connection attempts from external IPs',
  'Analyze sudden spike in traffic from a specific agent',
];

export function ChatInput({
  onSubmit,
  isLoading = false,
  prefilledQuery = '',
}: ChatInputProps) {
  const [input, setInput] = useState(prefilledQuery);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (prefilledQuery) {
      setInput(prefilledQuery);
    }
  }, [prefilledQuery]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      onSubmit(input);
      setInput('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && e.altKey) {
      handleSubmit(e as any);
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const target = e.target;
    setInput(target.value);
    target.style.height = 'auto';
    target.style.height = Math.min(target.scrollHeight, 120) + 'px';
  };

  return (
    <Card className="border-slate-700 bg-slate-800/50">
      <div className="p-4">
        <div className="mb-4 flex flex-wrap gap-2">
          {PRESET_CHIPS.map((chip) => (
            <button
              key={chip}
              onClick={() => {
                onSubmit(chip);
              }}
              className="rounded-full border border-slate-600 bg-slate-700/50 px-3 py-1 text-xs text-slate-300 hover:bg-slate-700 hover:text-white hover:border-cyan-500/50 transition-all"
            >
              {chip}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            placeholder="Ask about security events... (Alt+Enter to send)"
            className="w-full resize-none rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:border-cyan-500 focus:outline-none"
            style={{ maxHeight: '120px', minHeight: '80px' }}
          />
          <Button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="w-full bg-cyan-600 hover:bg-cyan-700 disabled:opacity-50"
          >
            {isLoading ? 'Sending...' : 'Send'}
          </Button>
        </form>
      </div>
    </Card>
  );
}
