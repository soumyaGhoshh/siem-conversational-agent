'use client';

import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import type { ChatResponse } from '@/lib/types';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { Badge } from '@/components/ui/badge';
import { Brain, AlertCircle, BookOpen, ShieldCheck, ChevronRight } from 'lucide-react';

interface ChatResponseTabsProps {
  response: ChatResponse;
  onSave?: (name: string) => void;
}

export function ChatResponseTabs({ response, onSave }: ChatResponseTabsProps) {
  const [selectedField, setSelectedField] = useState('user.name');
  const [saveName, setSaveName] = useState('');
  const [showSaveDialog, setShowSaveDialog] = useState(false);

  const timeSeriesData = response.aggregations?.byTime?.buckets || [];
  const topTermsBuckets = response.aggregations?.topTerms?.buckets || [];

  const handleSave = () => {
    if (saveName && onSave) {
      onSave(saveName);
      setSaveName('');
      setShowSaveDialog(false);
    }
  };

  return (
    <Card className="border-slate-700 bg-slate-800/50">
      <Tabs defaultValue="insight" className="w-full">
        <TabsList className="border-b border-slate-700 bg-slate-900/50">
          <TabsTrigger value="insight" className="gap-2">
            <Brain className="h-4 w-4" /> AI Insight
          </TabsTrigger>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="results">Results</TabsTrigger>
          <TabsTrigger value="dsl">DSL</TabsTrigger>
          <TabsTrigger value="saved">Saved</TabsTrigger>
        </TabsList>

        <TabsContent value="insight" className="p-6">
          <div className="space-y-6">
            {/* Severity and Analysis */}
            <div className="flex items-start justify-between">
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <h4 className="text-lg font-semibold text-white">Security Analysis</h4>
                  {response.severity && (
                    <Badge 
                      variant="outline" 
                      className={
                        response.severity === 'critical' ? 'border-red-500 text-red-400 bg-red-500/10' :
                        response.severity === 'high' ? 'border-orange-500 text-orange-400 bg-orange-500/10' :
                        response.severity === 'medium' ? 'border-yellow-500 text-yellow-400 bg-yellow-500/10' :
                        'border-blue-500 text-blue-400 bg-blue-500/10'
                      }
                    >
                      {response.severity.toUpperCase()}
                    </Badge>
                  )}
                </div>
                <p className="text-slate-300 leading-relaxed">
                  {response.analysis || "No analysis provided by the AI model."}
                </p>
              </div>
            </div>

            {/* Story / Attack Chain */}
            {response.story && (
              <div className="rounded-lg border border-cyan-500/30 bg-cyan-500/5 p-4">
                <div className="mb-4 flex items-center gap-2 text-cyan-400">
                  <BookOpen className="h-5 w-5" />
                  <h5 className="font-semibold">Attack Chain Visualization</h5>
                </div>
                
                <div className="flex flex-wrap items-center gap-2">
                  {response.story.split('->').map((step, idx, arr) => (
                    <div key={idx} className="flex items-center gap-2">
                      <div className="rounded-md bg-slate-800 px-3 py-1.5 text-sm font-medium text-slate-200 border border-slate-700">
                        {step.trim()}
                      </div>
                      {idx < arr.length - 1 && (
                        <ChevronRight className="h-4 w-4 text-slate-500" />
                      )}
                    </div>
                  ))}
                </div>
                
                <p className="mt-4 text-xs text-slate-400 italic">
                  Narrative: "{response.story}"
                </p>
              </div>
            )}

            {/* Remediation Suggestions */}
            {response.remediation && (
              <div className="rounded-lg border border-green-500/30 bg-green-500/5 p-4">
                <div className="mb-2 flex items-center gap-2 text-green-400">
                  <ShieldCheck className="h-5 w-5" />
                  <h5 className="font-semibold">Remediation Suggestion</h5>
                </div>
                <div className="flex items-center justify-between">
                  <p className="text-sm text-slate-300">
                    {response.remediation}
                  </p>
                  <Button variant="outline" size="sm" className="border-green-500/50 text-green-400 hover:bg-green-500/10">
                    Apply Fix
                  </Button>
                </div>
              </div>
            )}

            {!response.analysis && !response.story && (
              <div className="py-8 text-center text-slate-500">
                <AlertCircle className="mx-auto mb-2 h-8 w-8 opacity-20" />
                <p>No deep AI analysis available for this query.</p>
              </div>
            )}
          </div>
        </TabsContent>

        <TabsContent value="overview" className="p-6">
          <div className="space-y-6">
            {topTermsBuckets.length > 0 && (
              <div>
                <h4 className="mb-4 font-semibold text-white">Top-N Terms</h4>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={topTermsBuckets}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="key" stroke="#94a3b8" />
                    <YAxis stroke="#94a3b8" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1e293b',
                        border: '1px solid #475569',
                      }}
                    />
                    <Bar dataKey="doc_count" fill="#06b6d4" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}

            {timeSeriesData.length > 0 && (
              <div>
                <h4 className="mb-4 font-semibold text-white">Timeline</h4>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={timeSeriesData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="key_as_string" stroke="#94a3b8" />
                    <YAxis stroke="#94a3b8" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1e293b',
                        border: '1px solid #475569',
                      }}
                    />
                    <Line type="monotone" dataKey="doc_count" stroke="#06b6d4" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        </TabsContent>

        <TabsContent value="results" className="p-6">
          <div className="space-y-4">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-700">
                    {Object.keys(response.results.data[0] || {}).map((key) => (
                      <th
                        key={key}
                        className="px-4 py-2 text-left font-semibold text-slate-300"
                      >
                        {key}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {response.results.data.map((row, idx) => (
                    <tr
                      key={idx}
                      className="border-b border-slate-700/50 hover:bg-slate-700/30"
                    >
                      {Object.values(row).map((val, i) => (
                        <td key={i} className="px-4 py-2 text-slate-300">
                          {typeof val === 'string' || typeof val === 'number'
                            ? String(val).slice(0, 50)
                            : '—'}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="text-sm text-slate-400">
              Showing {response.results.data.length} of{' '}
              {response.results.totalHits} results
            </div>
          </div>
        </TabsContent>

        <TabsContent value="dsl" className="p-6">
          <div className="space-y-4">
            <pre className="max-h-96 overflow-auto rounded-md bg-slate-900 p-4 font-mono text-xs text-cyan-400">
              {response.queryGenerated}
            </pre>
            <Button className="bg-green-600 hover:bg-green-700">
              Download DSL
            </Button>
          </div>
        </TabsContent>

        <TabsContent value="saved" className="p-6">
          <div className="space-y-4">
            {!showSaveDialog ? (
              <Button
                onClick={() => setShowSaveDialog(true)}
                className="w-full bg-cyan-600 hover:bg-cyan-700"
              >
                Save This Query
              </Button>
            ) : (
              <div className="space-y-2">
                <input
                  type="text"
                  placeholder="Search name"
                  value={saveName}
                  onChange={(e) => setSaveName(e.target.value)}
                  className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white placeholder:text-slate-500"
                />
                <div className="flex gap-2">
                  <Button
                    onClick={handleSave}
                    disabled={!saveName}
                    className="flex-1 bg-green-600 hover:bg-green-700"
                  >
                    Save
                  </Button>
                  <Button
                    onClick={() => {
                      setShowSaveDialog(false);
                      setSaveName('');
                    }}
                    variant="outline"
                    className="flex-1"
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </Card>
  );
}
