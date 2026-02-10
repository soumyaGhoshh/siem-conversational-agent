'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { useAppStore } from '@/lib/store';

export function DashboardQuickActions() {
  const [refreshing, setRefreshing] = useState(false);
  const [testing, setTesting] = useState(false);
  const [refreshMessage, setRefreshMessage] = useState('');
  const [testMessage, setTestMessage] = useState('');

  const selectedIndex = useAppStore((state) => state.selectedIndex);
  const user = useAppStore((state) => state.user);

  const handleRefreshSchema = async () => {
    setRefreshing(true);
    setRefreshMessage('');
    try {
      const res = await fetch(`/api/schema?index=${selectedIndex || 'wazuh-alerts-*'}`, {
        headers: {
          'Authorization': user?.accessToken ? `Bearer ${user.accessToken}` : '',
        }
      });
      if (res.ok) {
        setRefreshMessage('✓ Schema refreshed successfully');
      } else {
        setRefreshMessage('Failed to refresh schema');
      }
    } catch {
      setRefreshMessage('Error refreshing schema');
    } finally {
      setRefreshing(false);
      setTimeout(() => setRefreshMessage(''), 3000);
    }
  };

  const handleTestConnection = async () => {
    setTesting(true);
    setTestMessage('');
    try {
      const res = await fetch('/api/preflight');
      if (res.ok) {
        setTestMessage('✓ Connection successful');
      } else {
        setTestMessage('Connection failed');
      }
    } catch {
      setTestMessage('Error testing connection');
    } finally {
      setTesting(false);
      setTimeout(() => setTestMessage(''), 3000);
    }
  };

  return (
    <Card className="border-slate-700 bg-slate-900/50 p-6">
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold text-white">Quick Actions</h3>
          <p className="text-sm text-slate-400">System maintenance</p>
        </div>

        <div className="space-y-2">
          <div className="flex gap-2">
            <Button
              onClick={handleRefreshSchema}
              disabled={refreshing}
              className="flex-1 bg-blue-600 hover:bg-blue-700"
            >
              {refreshing ? 'Refreshing...' : 'Refresh Schema'}
            </Button>
            <Button
              onClick={handleTestConnection}
              disabled={testing}
              className="flex-1 bg-green-600 hover:bg-green-700"
            >
              {testing ? 'Testing...' : 'Test Connection'}
            </Button>
          </div>

          {refreshMessage && (
            <div className="rounded-md bg-blue-500/10 px-3 py-2 text-sm text-blue-400">
              {refreshMessage}
            </div>
          )}
          {testMessage && (
            <div className="rounded-md bg-green-500/10 px-3 py-2 text-sm text-green-400">
              {testMessage}
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}
