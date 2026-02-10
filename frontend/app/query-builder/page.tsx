'use client';

import React from "react"

import { useState, useEffect } from 'react';
import { ProtectedRoute } from '@/components/protected-route';
import { SidebarIdentity } from '@/components/sidebar-identity';
import { ChatResponseTabs } from '@/components/chat-response-tabs';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { apiClient } from '@/lib/api-client';
import { useAppStore } from '@/lib/store';
import { validateOperatorForType, validateQueryValue, validateMaxLookback } from '@/lib/validation';
import type { Schema, SchemaField, QueryOperator, ChatResponse } from '@/lib/types';

export default function QueryBuilderPage() {
  const [schema, setSchema] = useState<Schema | null>(null);
  const [selectedField, setSelectedField] = useState('');
  const [operator, setOperator] = useState<QueryOperator>('term');
  const [value, setValue] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState<ChatResponse | null>(null);

  const selectedIndex = useAppStore((state) => state.selectedIndex);
  const maxResults = useAppStore((state) => state.maxResults);
  const timeRange = useAppStore((state) => state.timeRange);
  const user = useAppStore((state) => state.user);

  useEffect(() => {
    const fetchSchema = async () => {
      try {
        const data = await apiClient.getSchema(selectedIndex, user?.accessToken);
        setSchema(data);
        if (data.fields.length > 0) {
          setSelectedField(data.fields[0].name);
        }
      } catch (err) {
        console.error('Failed to fetch schema:', err);
      }
    };

    fetchSchema();
  }, [selectedIndex, user?.accessToken]);

  const getFieldType = (name: string): SchemaField['type'] | null => {
    return schema?.fields.find((f) => f.name === name)?.type || null;
  };

  const getValidOperators = (fieldType: SchemaField['type'] | null): QueryOperator[] => {
    if (!fieldType) return ['term'];
    if (fieldType === 'date') return ['term'];
    if (fieldType === 'text') return ['match', 'wildcard'];
    return ['term', 'match', 'wildcard'];
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};
    const fieldType = getFieldType(selectedField);

    if (!selectedField) {
      newErrors.field = 'Field is required';
    }

    const opError = validateOperatorForType(fieldType || 'text', operator);
    if (opError) {
      newErrors[opError.field] = opError.message;
    }

    const valError = validateQueryValue(value, fieldType || 'text', operator);
    if (valError) {
      newErrors[valError.field] = valError.message;
    }

    if (user?.role === 'analyst') {
      const lookbackError = validateMaxLookback(user.role, timeRange);
      if (lookbackError) {
        newErrors[lookbackError.field] = lookbackError.message;
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleRun = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) return;

    setIsLoading(true);
    try {
      const result = await apiClient.buildQuery(
        selectedField,
        operator,
        value,
        timeRange,
        maxResults,
        selectedIndex,
        user?.accessToken
      );
      setResponse(result);
    } catch (err) {
      console.error('Query error:', err);
      setErrors({ submit: 'Failed to execute query' });
    } finally {
      setIsLoading(false);
    }
  };

  const fieldType = getFieldType(selectedField);
  const validOperators = getValidOperators(fieldType);

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
                { href: '/query-builder', label: 'Query Builder', active: true },
                { href: '/saved-searches', label: 'Saved Searches' },
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
              <h2 className="text-3xl font-bold text-white">Query Builder</h2>
              <p className="text-slate-400">
                Create deterministic queries without writing DSL
              </p>
            </div>

            <div className="grid gap-6 lg:grid-cols-3">
              {/* Form */}
              <div className="lg:col-span-1">
                <Card className="border-slate-700 bg-slate-900/50 p-6">
                  <form onSubmit={handleRun} className="space-y-4">
                    <div>
                      <label className="text-sm font-medium text-slate-300">
                        Field
                      </label>
                      <Select value={selectedField} onValueChange={setSelectedField}>
                        <SelectTrigger className="mt-2 border-slate-700 bg-slate-800">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="border-slate-700 bg-slate-900">
                          {schema?.fields.map((field) => (
                            <SelectItem key={field.name} value={field.name}>
                              {field.name}
                              <span className="ml-2 text-xs text-slate-500">
                                ({field.type})
                              </span>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      {errors.field && (
                        <div className="mt-1 text-xs text-red-400">
                          {errors.field}
                        </div>
                      )}
                    </div>

                    <div>
                      <label className="text-sm font-medium text-slate-300">
                        Operator
                      </label>
                      <Select
                        value={operator}
                        onValueChange={(val) =>
                          setOperator(val as QueryOperator)
                        }
                      >
                        <SelectTrigger className="mt-2 border-slate-700 bg-slate-800">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="border-slate-700 bg-slate-900">
                          {validOperators.map((op) => (
                            <SelectItem key={op} value={op}>
                              {op}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      {errors.operator && (
                        <div className="mt-1 text-xs text-red-400">
                          {errors.operator}
                        </div>
                      )}
                    </div>

                    <div>
                      <label className="text-sm font-medium text-slate-300">
                        Value
                      </label>
                      <Input
                        type="text"
                        value={value}
                        onChange={(e) => setValue(e.target.value)}
                        placeholder="Enter value"
                        className="mt-2 border-slate-700 bg-slate-800 text-white"
                      />
                      {errors.value && (
                        <div className="mt-1 text-xs text-red-400">
                          {errors.value}
                        </div>
                      )}
                    </div>

                    {errors.timeRange && (
                      <div className="rounded-md border border-yellow-500/30 bg-yellow-500/10 p-3 text-xs text-yellow-400">
                        {errors.timeRange}
                      </div>
                    )}

                    {errors.submit && (
                      <div className="rounded-md border border-red-500/30 bg-red-500/10 p-3 text-xs text-red-400">
                        {errors.submit}
                      </div>
                    )}

                    <Button
                      type="submit"
                      disabled={isLoading}
                      className="w-full bg-cyan-600 hover:bg-cyan-700"
                    >
                      {isLoading ? 'Running...' : 'Run Query'}
                    </Button>
                  </form>
                </Card>
              </div>

              {/* Results */}
              {response && (
                <div className="lg:col-span-2">
                  <ChatResponseTabs response={response} />
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    </ProtectedRoute>
  );
}
