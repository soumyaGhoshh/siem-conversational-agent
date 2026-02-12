'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Shield, AlertTriangle, Users, Target } from 'lucide-react';
import { apiClient } from '@/lib/api-client';
import { useAppStore } from '@/lib/store';

export function QuickStats() {
  const [stats, setStats] = useState<any>(null);
  const selectedIndex = useAppStore((state) => state.selectedIndex);
  const user = useAppStore((state) => state.user);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await apiClient.getStats(selectedIndex, user?.accessToken);
        setStats(data);
      } catch (err) {
        console.error('Failed to fetch stats:', err);
      }
    };
    fetchStats();
  }, [selectedIndex, user?.accessToken]);

  const items = [
    {
      label: 'Total Alerts (24h)',
      value: stats?.totalAlerts || 0,
      icon: Shield,
      color: 'text-blue-400',
      bg: 'bg-blue-500/10',
    },
    {
      label: 'High Severity',
      value: stats?.highSeverity || 0,
      icon: AlertTriangle,
      color: 'text-red-400',
      bg: 'bg-red-500/10',
    },
    {
      label: 'Active Agents',
      value: stats?.activeAgents || 0,
      icon: Users,
      color: 'text-green-400',
      bg: 'bg-green-500/10',
    },
    {
      label: 'Top Attacker',
      value: stats?.topAttacker || 'N/A',
      icon: Target,
      color: 'text-yellow-400',
      bg: 'bg-yellow-500/10',
    },
  ];

  return (
    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 lg:col-span-3">
      {items.map((item) => (
        <Card key={item.label} className="border-slate-700 bg-slate-900/50 p-6">
          <div className="flex items-center gap-4">
            <div className={`rounded-lg ${item.bg} p-3`}>
              <item.icon className={`h-6 w-6 ${item.color}`} />
            </div>
            <div>
              <p className="text-sm text-slate-400">{item.label}</p>
              <p className="text-2xl font-bold text-white">{item.value}</p>
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
}
