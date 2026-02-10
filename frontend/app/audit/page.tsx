'use client';

import { useState, useEffect } from 'react';
import { useAppStore } from '@/lib/store';
import { ProtectedRoute } from '@/components/protected-route';
import { SidebarIdentity } from '@/components/sidebar-identity';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { apiClient } from '@/lib/api-client';
import type { AuditEntry } from '@/lib/types';

export default function AuditPage() {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filterUser, setFilterUser] = useState('');
  const [filterIndex, setFilterIndex] = useState('');

  const user = useAppStore((state) => state.user);

  useEffect(() => {
    const fetchAudit = async () => {
      try {
        const data = await apiClient.getAudit(user?.accessToken);
        setEntries(data);
      } catch (err) {
        console.error('Failed to fetch audit:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchAudit();
  }, [user?.accessToken]);

  const filteredEntries = entries.filter((entry) => {
    if (filterUser && entry.user !== filterUser) return false;
    if (filterIndex && entry.index !== filterIndex) return false;
    return true;
  });

  const uniqueUsers = [...new Set(entries.map((e) => e.user))];
  const uniqueIndices = [...new Set(entries.map((e) => e.index))];

  const formatDate = (ts: number) => {
    return new Date(ts).toLocaleString();
  };

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  return (
    <ProtectedRoute>
      <div className="flex min-h-screen bg-slate-950">
        {/* Sidebar */}
        <aside className="w-64 border-r border-slate-700 bg-slate-900 p-6">
          <div className="space-y-8">
            <div>
              <h1 className="text-2xl font-bold text-cyan-400">AI SIEM</h1>
              <p className="text-xs text-slate-500">Security Operations</p>
            </div>

            <SidebarIdentity />

            <nav className="space-y-2">
              {[
                { href: '/dashboard', label: 'Dashboard' },
                { href: '/chat', label: 'Chat' },
                { href: '/query-builder', label: 'Query Builder' },
                { href: '/saved-searches', label: 'Saved Searches' },
                { href: '/audit', label: 'Audit', active: true },
              ].map((item) => (
                <a
                  key={item.href}
                  href={item.href}
                  className={`block rounded px-3 py-2 text-sm ${
                    item.active
                      ? 'bg-cyan-600 text-white'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {item.label}
                </a>
              ))}
            </nav>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-auto p-8">
          <div className="mx-auto max-w-6xl">
            <div className="mb-8">
              <h2 className="text-3xl font-bold text-white">Audit Log</h2>
              <p className="text-slate-400">
                Recent query executions and system activities
              </p>
            </div>

            {/* Filters */}
            <div className="mb-6 grid gap-4 md:grid-cols-2">
              <div>
                <label className="text-sm font-medium text-slate-300">
                  Filter by User
                </label>
                <Select value={filterUser} onValueChange={setFilterUser}>
                  <SelectTrigger className="mt-2 border-slate-700 bg-slate-800">
                    <SelectValue placeholder="All users" />
                  </SelectTrigger>
                  <SelectContent className="border-slate-700 bg-slate-900">
                    <SelectItem value="all-users">All users</SelectItem>
                    {uniqueUsers.map((user) => (
                      <SelectItem key={user} value={user}>
                        {user}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label className="text-sm font-medium text-slate-300">
                  Filter by Index
                </label>
                <Select value={filterIndex} onValueChange={setFilterIndex}>
                  <SelectTrigger className="mt-2 border-slate-700 bg-slate-800">
                    <SelectValue placeholder="All indices" />
                  </SelectTrigger>
                  <SelectContent className="border-slate-700 bg-slate-900">
                    <SelectItem value="all-indices">All indices</SelectItem>
                    {uniqueIndices.map((idx) => (
                      <SelectItem key={idx} value={idx}>
                        {idx}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Table */}
            {isLoading ? (
              <Card className="border-slate-700 bg-slate-900/50 p-8">
                <div className="text-center text-slate-400">Loading...</div>
              </Card>
            ) : filteredEntries.length === 0 ? (
              <Card className="border-slate-700 bg-slate-900/50 p-8">
                <div className="text-center text-slate-400">
                  No audit entries found
                </div>
              </Card>
            ) : (
              <Card className="border-slate-700 bg-slate-900/50 overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-700 bg-slate-800/50">
                        <th className="px-6 py-3 text-left font-semibold text-slate-300">
                          Timestamp
                        </th>
                        <th className="px-6 py-3 text-left font-semibold text-slate-300">
                          User
                        </th>
                        <th className="px-6 py-3 text-left font-semibold text-slate-300">
                          Index
                        </th>
                        <th className="px-6 py-3 text-right font-semibold text-slate-300">
                          Results
                        </th>
                        <th className="px-6 py-3 text-right font-semibold text-slate-300">
                          Duration
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredEntries.map((entry, idx) => (
                        <tr
                          key={idx}
                          className="border-b border-slate-700/50 hover:bg-slate-800/30"
                        >
                          <td className="px-6 py-4 text-slate-300">
                            {formatDate(entry.ts)}
                          </td>
                          <td className="px-6 py-4">
                            <span className="inline-block rounded-full bg-slate-700 px-2 py-1 text-xs text-slate-200">
                              {entry.user}
                            </span>
                          </td>
                          <td className="px-6 py-4 font-mono text-slate-300">
                            {entry.index}
                          </td>
                          <td className="px-6 py-4 text-right text-slate-300">
                            <span className="font-semibold text-cyan-400">
                              {entry.hits}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-right text-slate-300">
                            {formatDuration(entry.durationMs)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>
            )}
          </div>
        </main>
      </div>
    </ProtectedRoute>
  );
}
