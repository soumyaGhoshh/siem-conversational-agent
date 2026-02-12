'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { StatusIndicator } from '@/components/status-indicator';
import { apiClient } from '@/lib/api-client';
import type { PreflightStatus } from '@/lib/types';

export function DashboardPreflight() {
  const [status, setStatus] = useState<PreflightStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const data = await apiClient.getPreflight();
        setStatus(data);
      } catch (err) {
        console.error('Failed to fetch preflight:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchStatus();
  }, []);

  if (isLoading) {
    return (
      <Card className="border-slate-700 bg-slate-900/50 p-6">
        <div className="text-center text-slate-400">Loading...</div>
      </Card>
    );
  }

  if (!status) {
    return (
      <Card className="border-slate-700 bg-slate-900/50 p-6">
        <div className="text-center text-red-400">Failed to load preflight</div>
      </Card>
    );
  }

  const isReady = Object.values(status).every((v) => v);

  return (
    <Card className="border-slate-700 bg-slate-900/50 p-6">
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold text-white">Preflight Check</h3>
          <p className="text-sm text-slate-400">System readiness status</p>
        </div>

        <div className="space-y-3">
          <StatusIndicator label="Elasticsearch" status={status.esOk} />
          <StatusIndicator label="Credentials" status={status.credsOk} />
          <StatusIndicator label="LLM" status={status.llmOk} />
          <StatusIndicator label="Schema" status={status.schemaOk} />
        </div>

        <div className="rounded-md border border-slate-700 bg-slate-800/30 p-3">
          <div className="text-sm">
            <span className="text-slate-400">Status: </span>
            <span className={isReady ? 'text-cyan-400 font-semibold' : 'text-red-400'}>
              {isReady ? '✓ Ready for queries' : '✗ System not ready'}
            </span>
          </div>
        </div>
      </div>
    </Card>
  );
}
