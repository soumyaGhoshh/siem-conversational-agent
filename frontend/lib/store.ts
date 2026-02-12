import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { User, AuditEntry, SavedSearch, TimeRange } from './types';

interface AppState {
  user: User | null;
  auditLogs: AuditEntry[];
  savedSearches: SavedSearch[];
  isLoading: boolean;
  setUser: (user: User | null) => void;
  setAuditLogs: (logs: AuditEntry[]) => void;
  setSavedSearches: (searches: SavedSearch[]) => void;
  setIsLoading: (loading: boolean) => void;
  logout: () => void;
  isAuthenticated: () => boolean;

  selectedIndex: string;
  setSelectedIndex: (index: string) => void;

  maxResults: number;
  setMaxResults: (count: number) => void;

  rowsPerPage: number;
  setRowsPerPage: (count: number) => void;

  timeRange: TimeRange;
  setTimeRange: (range: TimeRange) => void;

  allowedIndices: string[];
  setAllowedIndices: (indices: string[]) => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      user: null,
      auditLogs: [],
      savedSearches: [],
      isLoading: false,
      setUser: (user) => set({ user }),
      setAuditLogs: (auditLogs) => set({ auditLogs }),
      setSavedSearches: (savedSearches) => set({ savedSearches }),
      setIsLoading: (isLoading) => set({ isLoading }),
      logout: () => {
        set({ user: null, auditLogs: [], savedSearches: [] });
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
      },
      isAuthenticated: () => {
        const user = get().user;
        return !!(user && user.accessToken);
      },

      selectedIndex: 'wazuh-alerts-*',
      setSelectedIndex: (index) => set({ selectedIndex: index }),

      maxResults: 100,
      setMaxResults: (count) => set({ maxResults: count }),

      rowsPerPage: 10,
      setRowsPerPage: (count) => set({ rowsPerPage: count }),

      timeRange: '24h',
      setTimeRange: (range) => set({ timeRange: range }),

      allowedIndices: ['wazuh-alerts-*', 'wazuh-archives-*'],
      setAllowedIndices: (indices) => set({ allowedIndices: indices }),
    }),
    {
      name: 'siem-app-storage',
      storage: createJSONStorage(() => localStorage),
    }
  )
);
