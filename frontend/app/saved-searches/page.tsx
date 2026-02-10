'use client';

import { useState, useEffect } from 'react';
import { useAppStore } from '@/lib/store';
import { ProtectedRoute } from '@/components/protected-route';
import { SidebarIdentity } from '@/components/sidebar-identity';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { apiClient } from '@/lib/api-client';
import type { SavedSearch } from '@/lib/types';

export default function SavedSearchesPage() {
  const [searches, setSearches] = useState<SavedSearch[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [runningId, setRunningId] = useState<number | null>(null);

  const user = useAppStore((state) => state.user);

  useEffect(() => {
    const fetchSearches = async () => {
      try {
        const data = await apiClient.getSavedSearches(user?.accessToken);
        setSearches(data);
      } catch (err) {
        console.error('Failed to fetch saved searches:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSearches();
  }, [user?.accessToken]);

  const handleRun = async (id: number) => {
    setRunningId(id);
    try {
      await apiClient.runSavedSearch(id, user?.accessToken);
      // In a full implementation, show results in a modal or navigate to results
      alert('Search executed successfully');
    } catch (err) {
      console.error('Failed to run search:', err);
      alert('Failed to run search');
    } finally {
      setRunningId(null);
    }
  };

  const handleDelete = (id: number) => {
    if (confirm('Delete this saved search?')) {
      setSearches((prev) => prev.filter((s) => s.id !== id));
    }
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
                { href: '/saved-searches', label: 'Saved Searches', active: true },
                { href: '/audit', label: 'Audit' },
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
          <div className="mx-auto max-w-4xl">
            <div className="mb-8">
              <h2 className="text-3xl font-bold text-white">Saved Searches</h2>
              <p className="text-slate-400">
                Manage and run your saved threat queries
              </p>
            </div>

            {isLoading ? (
              <Card className="border-slate-700 bg-slate-900/50 p-8">
                <div className="text-center text-slate-400">Loading...</div>
              </Card>
            ) : searches.length === 0 ? (
              <Card className="border-slate-700 bg-slate-900/50 p-8">
                <div className="text-center">
                  <div className="mb-2 text-slate-400">No saved searches yet</div>
                  <div className="text-sm text-slate-500">
                    Create searches in the Chat or Query Builder
                  </div>
                </div>
              </Card>
            ) : (
              <div className="space-y-4">
                {searches.map((search) => (
                  <Card
                    key={search.id}
                    className="border-slate-700 bg-slate-900/50 p-4"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="font-semibold text-white">
                          {search.name}
                        </h3>
                        <p className="text-sm text-slate-400">
                          Index: {search.index}
                        </p>
                        {search.queryJson && (
                          <div className="mt-2 max-h-24 overflow-auto rounded-md bg-slate-950 p-2 font-mono text-xs text-slate-400">
                            {search.queryJson}
                          </div>
                        )}
                      </div>

                      <div className="ml-4 flex gap-2">
                        <Button
                          onClick={() => handleRun(search.id)}
                          disabled={runningId === search.id}
                          className="bg-cyan-600 hover:bg-cyan-700"
                        >
                          {runningId === search.id ? 'Running...' : 'Run'}
                        </Button>
                        <Button
                          onClick={() => handleDelete(search.id)}
                          variant="destructive"
                          className="bg-red-600 hover:bg-red-700"
                        >
                          Delete
                        </Button>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </main>
      </div>
    </ProtectedRoute>
  );
}
