'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, LineChart, Line } from 'recharts';
import { apiClient } from '@/lib/api-client';
import { useAppStore } from '@/lib/store';

export function SystemStats() {
  const [stats, setStats] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const selectedIndex = useAppStore((state) => state.selectedIndex);
  const user = useAppStore((state) => state.user);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        // Fetching stats which should include aggregations
        const data = await apiClient.getStats(selectedIndex, user?.accessToken);
        setStats(data);
      } catch (err) {
        console.error('Failed to fetch stats:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchStats();
  }, [selectedIndex, user?.accessToken]);

  if (isLoading) return <div className="text-slate-400">Loading charts...</div>;

  const topTerms = stats?.aggregations?.top_terms?.buckets || [];
  const timeline = stats?.aggregations?.by_time?.buckets || [];

  return (
    <div className="grid gap-6 md:grid-cols-2 lg:col-span-2">
      <Card className="border-slate-700 bg-slate-900/50 p-6">
        <h3 className="mb-6 text-lg font-semibold text-white">Top Alert Categories</h3>
        <div className="h-64 w-full flex items-center justify-center">
          {topTerms.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={topTerms}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                <XAxis dataKey="key" stroke="#94a3b8" fontSize={10} tickLine={false} axisLine={false} />
                <YAxis stroke="#94a3b8" fontSize={10} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }}
                  itemStyle={{ color: '#06b6d4' }}
                />
                <Bar dataKey="doc_count" fill="#06b6d4" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-sm text-slate-500 italic">No category data found for this period.</div>
          )}
        </div>
      </Card>

      <Card className="border-slate-700 bg-slate-900/50 p-6">
        <h3 className="mb-6 text-lg font-semibold text-white">Alert Timeline</h3>
        <div className="h-64 w-full flex items-center justify-center">
          {timeline.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={timeline}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                <XAxis dataKey="key_as_string" stroke="#94a3b8" fontSize={10} tickLine={false} axisLine={false} />
                <YAxis stroke="#94a3b8" fontSize={10} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }}
                  itemStyle={{ color: '#06b6d4' }}
                />
                <Line type="monotone" dataKey="doc_count" stroke="#06b6d4" strokeWidth={2} dot={{ r: 4, fill: '#06b6d4' }} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-sm text-slate-500 italic">No timeline data found for this period.</div>
          )}
        </div>
      </Card>
    </div>
  );
}
