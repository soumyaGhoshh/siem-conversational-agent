import type { SchemaField, QueryOperator } from './types';

export interface ValidationError {
  field: string;
  message: string;
}

export function validateOperatorForType(
  type: string,
  operator: QueryOperator
): ValidationError | null {
  const wildcardTypes = ['keyword', 'text'];
  const numericTypes = ['integer', 'long', 'float', 'double'];
  const dateTypes = ['date'];

  if (operator === 'wildcard' && !wildcardTypes.includes(type)) {
    return {
      field: 'operator',
      message: 'Wildcard only works on keyword/text fields',
    };
  }

  if ((operator === 'term' || operator === 'match') && dateTypes.includes(type)) {
    return {
      field: 'operator',
      message: 'Use term/match on keyword or text fields, not dates',
    };
  }

  return null;
}

export function validateQueryValue(
  value: string | number,
  type: string,
  operator: QueryOperator
): ValidationError | null {
  if (!value) {
    return { field: 'value', message: 'Value is required' };
  }

  const numericTypes = ['integer', 'long', 'float', 'double'];
  if (numericTypes.includes(type) && isNaN(Number(value))) {
    return { field: 'value', message: 'Value must be numeric' };
  }

  if (operator === 'wildcard' && typeof value === 'string') {
    // Wildcard values should be strings, this is fine
  }

  return null;
}

export function validateMaxLookback(
  role: string,
  timeRange: string
): ValidationError | null {
  if (role === 'analyst' && timeRange === '7d') {
    return {
      field: 'timeRange',
      message: 'Analysts are limited to 24h lookback. Contact admin for extended access.',
    };
  }

  return null;
}
