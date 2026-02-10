'use client';

import { Card } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { useAppStore } from '@/lib/store';

export function DashboardSettings() {
  const {
    selectedIndex,
    setSelectedIndex,
    maxResults,
    setMaxResults,
    timeRange,
    setTimeRange,
    allowedIndices,
  } = useAppStore();

  return (
    <Card className="border-slate-700 bg-slate-900/50 p-6">
      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-semibold text-white">Global Settings</h3>
          <p className="text-sm text-slate-400">Configure your session parameters</p>
        </div>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label className="text-slate-300">Index Pattern</Label>
            <Select value={selectedIndex} onValueChange={setSelectedIndex}>
              <SelectTrigger className="bg-slate-800 border-slate-700 text-slate-200">
                <SelectValue placeholder="Select index" />
              </SelectTrigger>
              <SelectContent className="bg-slate-800 border-slate-700">
                {allowedIndices.map((idx) => (
                  <SelectItem key={idx} value={idx} className="text-slate-200">
                    {idx}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label className="text-slate-300">Time Range</Label>
            <Select value={timeRange} onValueChange={(val: any) => setTimeRange(val)}>
              <SelectTrigger className="bg-slate-800 border-slate-700 text-slate-200">
                <SelectValue placeholder="Select range" />
              </SelectTrigger>
              <SelectContent className="bg-slate-800 border-slate-700">
                <SelectItem value="1h" className="text-slate-200">Last 1 hour</SelectItem>
                <SelectItem value="24h" className="text-slate-200">Last 24 hours</SelectItem>
                <SelectItem value="7d" className="text-slate-200">Last 7 days</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-4">
            <div className="flex justify-between">
              <Label className="text-slate-300">Max Results</Label>
              <span className="text-xs text-cyan-400 font-mono">{maxResults}</span>
            </div>
            <Slider
              value={[maxResults]}
              onValueChange={(val) => setMaxResults(val[0])}
              min={10}
              max={500}
              step={10}
              className="py-4"
            />
          </div>
        </div>
      </div>
    </Card>
  );
}
