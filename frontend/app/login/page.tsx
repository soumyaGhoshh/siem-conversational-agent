'use client';

import React from "react"

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAppStore } from '@/lib/store';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { UserRole } from '@/lib/types';

export default function LoginPage() {
  const router = useRouter();
  const setUser = useAppStore((state) => state.setUser);
  
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      if (!username || !password) {
        setError('Username and password are required');
        setIsLoading(false);
        return;
      }

      // Validate against backend login endpoint
      const res = await fetch('http://127.0.0.1:8000/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      if (!res.ok) {
        const errData = await res.json();
        setError(errData.detail || 'Authentication failed');
        setIsLoading(false);
        return;
      }

      const data = await res.json();
      
      setUser({
        username,
        role: data.role,
        accessToken: data.token,
      });

      router.push('/dashboard');
    } catch (err) {
      setError('Connection to server failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-950 via-blue-950 to-slate-900 px-4">
      <Card className="w-full max-w-md border-slate-700 bg-slate-900/50 backdrop-blur-sm">
        <div className="space-y-6 p-8">
          <div className="space-y-2">
            <h1 className="text-3xl font-bold text-white">AI SIEM</h1>
            <p className="text-slate-400">Enterprise Security Operations</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <label
                htmlFor="username"
                className="text-sm font-medium text-slate-300"
              >
                Username
              </label>
              <Input
                id="username"
                type="text"
                placeholder="analyst@company.com"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="border-slate-700 bg-slate-800/50 text-white placeholder:text-slate-500"
              />
            </div>

            <div className="space-y-2">
              <label
                htmlFor="password"
                className="text-sm font-medium text-slate-300"
              >
                Password
              </label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="border-slate-700 bg-slate-800/50 text-white placeholder:text-slate-500"
              />
            </div>

            {error && (
              <div className="rounded-md border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-400">
                {error}
              </div>
            )}

            <Button
              type="submit"
              disabled={isLoading}
              className="w-full bg-cyan-600 hover:bg-cyan-700"
            >
              {isLoading ? 'Authenticating...' : 'Sign In'}
            </Button>
          </form>

          <div className="space-y-2 border-t border-slate-700 pt-4">
            <p className="text-xs text-slate-500">Demo Credentials</p>
            <div className="space-y-1 rounded-md bg-slate-800/30 p-3 font-mono text-xs text-slate-400">
              <div>
                <span className="text-slate-500">User: </span>analyst1
              </div>
              <div>
                <span className="text-slate-500">Pass: </span>changeme
              </div>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
