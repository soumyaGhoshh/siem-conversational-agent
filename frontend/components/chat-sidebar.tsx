'use client';

import { useAppStore } from '@/lib/store';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { SigmaMiniGallery } from '@/components/sigma-mini-gallery';
import { SidebarIdentity } from '@/components/sidebar-identity';

interface ChatSidebarProps {
  allowedIndices: string[];
}

export function ChatSidebar({ allowedIndices }: ChatSidebarProps) {
  const selectedIndex = useAppStore((state) => state.selectedIndex);
  const setSelectedIndex = useAppStore((state) => state.setSelectedIndex);
  const maxResults = useAppStore((state) => state.maxResults);
  const setMaxResults = useAppStore((state) => state.setMaxResults);
  const rowsPerPage = useAppStore((state) => state.rowsPerPage);
  const setRowsPerPage = useAppStore((state) => state.setRowsPerPage);
  const timeRange = useAppStore((state) => state.timeRange);
  const setTimeRange = useAppStore((state) => state.setTimeRange);

  return (
    <aside className="w-72 space-y-4 border-r border-slate-700 bg-slate-900 p-4 overflow-y-auto">
      <SidebarIdentity />

      <Card className="border-slate-700 bg-slate-800/50 p-4">
        <div className="space-y-3">
          <div>
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wide">
              Index Pattern
            </label>
            <Select value={selectedIndex} onValueChange={setSelectedIndex}>
              <SelectTrigger className="mt-2 border-slate-700 bg-slate-900">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="border-slate-700 bg-slate-900">
                {allowedIndices.map((idx) => (
                  <SelectItem key={idx} value={idx}>
                    {idx}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <label className="flex items-center justify-between text-xs font-semibold text-slate-300 uppercase tracking-wide">
              <span>Max Results</span>
              <span className="font-mono text-cyan-400">{maxResults}</span>
            </label>
            <Slider
              value={[maxResults]}
              onValueChange={(val) => setMaxResults(val[0])}
              min={10}
              max={500}
              step={10}
              className="mt-2"
            />
          </div>

          <div>
            <label className="flex items-center justify-between text-xs font-semibold text-slate-300 uppercase tracking-wide">
              <span>Rows Per Page</span>
              <span className="font-mono text-cyan-400">{rowsPerPage}</span>
            </label>
            <Slider
              value={[rowsPerPage]}
              onValueChange={(val) => setRowsPerPage(val[0])}
              min={5}
              max={100}
              step={5}
              className="mt-2"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wide">
              Time Range
            </label>
            <div className="mt-2 space-y-2">
              {(['1h', '24h', '7d'] as const).map((range) => (
                <label key={range} className="flex items-center gap-2">
                  <input
                    type="radio"
                    name="timeRange"
                    value={range}
                    checked={timeRange === range}
                    onChange={() => setTimeRange(range)}
                    className="h-3 w-3 rounded-full"
                  />
                  <span className="text-sm text-slate-300">{range}</span>
                </label>
              ))}
            </div>
          </div>
        </div>
      </Card>

      <SigmaMiniGallery />
    </aside>
  );
}
