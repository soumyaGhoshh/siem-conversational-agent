export type UserRole = 'analyst' | 'admin';

export interface User {
  username: string;
  role: UserRole;
  accessToken: string;
}

export interface PreflightStatus {
  esOk: boolean;
  credsOk: boolean;
  llmOk: boolean;
  schemaOk: boolean;
}

export interface SchemaField {
  name: string;
  type: 'keyword' | 'text' | 'date' | 'integer' | 'long' | 'float' | 'double';
}

export interface Schema {
  index: string;
  fields: SchemaField[];
}

export interface ChatResponse {
  queryGenerated: string;
  results: {
    totalHits: number;
    data: Record<string, any>[];
  };
  aggregations?: {
    topTerms?: {
      buckets: Array<{ key: string; doc_count: number }>;
    };
    byTime?: {
      buckets: Array<{ key_as_string: string; doc_count: number }>;
    };
  };
  analysis?: string;
  story?: string;
  remediation?: string;
  severity?: 'low' | 'medium' | 'high' | 'critical';
}

export interface AuditEntry {
  ts: number;
  user: string;
  index: string;
  hits: number;
  durationMs: number;
}

export interface SavedSearch {
  id: number;
  name: string;
  index: string;
  queryJson?: string;
}

export type TimeRange = '1h' | '24h' | '7d';
export type QueryOperator = 'term' | 'match' | 'wildcard';
