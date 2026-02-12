'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, ShieldAlert, Zap, BellRing } from 'lucide-react';
import { apiClient } from '@/lib/api-client';
import { useAppStore } from '@/lib/store';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';

interface Alert {
  id: string;
  timestamp: string;
  description: string;
  level: number;
  agent: string;
}

export function ProactiveAlerts() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [lastAlertId, setLastAlertId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const selectedIndex = useAppStore((state) => state.selectedIndex);
  const user = useAppStore((state) => state.user);
  const router = useRouter();

  useEffect(() => {
    // Initial fetch for historical context
    const fetchInitialAlerts = async () => {
      setIsLoading(true);
      try {
        const res = await apiClient.getRecentAlerts(selectedIndex, 12, user?.accessToken);
        setAlerts(res || []);
        if (res && res.length > 0) {
          setLastAlertId(res[0].id);
        }
      } catch (err) {
        console.error('Failed to fetch initial alerts:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchInitialAlerts();

    // Setup SSE for real-time updates
    const streamUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/alerts/stream?index=${selectedIndex}`;
    const eventSource = new EventSource(streamUrl);

    eventSource.onmessage = (event) => {
      try {
        const newAlert = JSON.parse(event.data);
        
        setAlerts(prev => {
          // Check if alert already exists to avoid duplicates
          if (prev.find(a => a.id === newAlert.id)) return prev;
          
          const updated = [newAlert, ...prev].slice(0, 12);
          
          // Toast for new alert
          toast.error(`NEW Critical Threat: ${newAlert.description}`, {
            description: `Detected on ${newAlert.agent} at ${new Date(newAlert.timestamp).toLocaleTimeString()}`,
            icon: <BellRing className="h-4 w-4" />,
            action: {
              label: 'Analyze',
              onClick: () => router.push(`/chat?q=analyze alert ${newAlert.id}`),
            },
          });
          
          return updated;
        });
      } catch (err) {
        console.error('Error parsing SSE event:', err);
      }
    };

    eventSource.onerror = (err) => {
      console.error('SSE connection error:', err);
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [selectedIndex, user?.accessToken]);

  if (alerts.length === 0 && !isLoading) return null;

  return (
    <Card className="border-red-900/50 bg-red-950/10 p-6 lg:col-span-2">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ShieldAlert className="h-5 w-5 text-red-500" />
          <h3 className="text-lg font-semibold text-white">Critical Threats Detected</h3>
        </div>
        <Badge variant="destructive" className="animate-pulse">
          Proactive Analysis Active
        </Badge>
      </div>

      <div className="space-y-3">
        {isLoading && alerts.length === 0 ? (
          <div className="py-4 text-center text-slate-500">Scanning for threats...</div>
        ) : (
          alerts.map((alert, idx) => (
            <div 
              key={alert.id || `alert-${idx}`}
              onClick={() => router.push(`/chat?q=analyze alert ${alert.id}`)}
              className="group flex cursor-pointer items-start gap-4 rounded-lg border border-slate-800 bg-slate-900/50 p-3 transition-colors hover:border-red-500/50 hover:bg-red-500/5"
            >
              <div className="mt-1 rounded-full bg-red-500/10 p-2">
                <Zap className="h-4 w-4 text-red-500" />
              </div>
              <div className="flex-1 space-y-1">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-slate-200 group-hover:text-white">
                    {alert.description}
                  </p>
                  <span className="text-xs text-slate-500">
                    {new Date(alert.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="border-red-500/30 text-red-400 text-[10px]">
                    Level {alert.level}
                  </Badge>
                  <span className="text-[10px] text-slate-500">
                    Agent: {alert.agent}
                  </span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </Card>
  );
}
