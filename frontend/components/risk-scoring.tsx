'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { apiClient } from '@/lib/api-client';
import { useAppStore } from '@/lib/store';

interface RiskEntry {
  entity: string;
  score: number;
}

export function RiskScoring() {
  const [data, setData] = useState<RiskEntry[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const selectedIndex = useAppStore((state) => state.selectedIndex);
  const user = useAppStore((state) => state.user);

  useEffect(() => {
    const fetchRisk = async () => {
      setIsLoading(true);
      try {
        const res = await apiClient.getStats(selectedIndex, user?.accessToken);
        
        if (res && res.riskScoring) {
          // Normalize score to 0-100 if it's based on Wazuh rule levels which can be high
          // Or just use as is if we want the raw level sum
          const normalizedData = res.riskScoring.map((item: any) => ({
            entity: item.entity || 'Unknown',
            score: Math.min(item.score, 100) // Simple cap for UI display
          }));
          setData(normalizedData);
        } else {
          setData([]);
        }
      } catch (err) {
        console.error('Failed to fetch risk scoring:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchRisk();
  }, [selectedIndex, user?.accessToken]);

  return (
    <Card className="border-slate-700 bg-slate-900/50 p-6">
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold text-white">Risk Scoring</h3>
          <p className="text-sm text-slate-400">Top entities by calculated risk</p>
        </div>

        <Table>
          <TableHeader>
            <TableRow className="border-slate-700 hover:bg-transparent">
              <TableHead className="text-slate-400">Entity</TableHead>
              <TableHead className="text-right text-slate-400">Risk Score</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((entry, idx) => (
              <TableRow key={`${entry.entity}-${idx}`} className="border-slate-800 hover:bg-slate-800/30">
                <TableCell className="font-medium text-slate-200">{entry.entity}</TableCell>
                <TableCell className="text-right">
                  <Badge 
                    variant="outline" 
                    className={
                      entry.score > 80 ? 'border-red-500 text-red-400' :
                      entry.score > 50 ? 'border-yellow-500 text-yellow-400' :
                      'border-green-500 text-green-400'
                    }
                  >
                    {entry.score}
                  </Badge>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </Card>
  );
}
