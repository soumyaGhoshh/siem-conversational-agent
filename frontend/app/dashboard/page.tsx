'use client';

import { ProtectedRoute } from '@/components/protected-route';
import { DashboardPreflight } from '@/components/dashboard-preflight';
import { DashboardQuickActions } from '@/components/dashboard-quick-actions';
import { DashboardSettings } from '@/components/dashboard-settings';
import { SigmaMiniGallery } from '@/components/sigma-mini-gallery';
import { RiskScoring } from '@/components/risk-scoring';
import { SystemStats } from '@/components/system-stats';
import { QuickStats } from '@/components/quick-stats';
import { ProactiveAlerts } from '@/components/proactive-alerts';
import { SidebarIdentity } from '@/components/sidebar-identity';
import { Button } from '@/components/ui/button';
import Link from 'next/link';

export default function DashboardPage() {
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
              <Link href="/dashboard">
                <Button
                  variant="ghost"
                  className="w-full justify-start text-slate-300 hover:text-white"
                >
                  Dashboard
                </Button>
              </Link>
              <Link href="/chat">
                <Button
                  variant="ghost"
                  className="w-full justify-start text-slate-300 hover:text-white"
                >
                  Chat
                </Button>
              </Link>
              <Link href="/query-builder">
                <Button
                  variant="ghost"
                  className="w-full justify-start text-slate-300 hover:text-white"
                >
                  Query Builder
                </Button>
              </Link>
              <Link href="/saved-searches">
                <Button
                  variant="ghost"
                  className="w-full justify-start text-slate-300 hover:text-white"
                >
                  Saved Searches
                </Button>
              </Link>
              <Link href="/audit">
                <Button
                  variant="ghost"
                  className="w-full justify-start text-slate-300 hover:text-white"
                >
                  Audit
                </Button>
              </Link>
            </nav>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-auto p-8">
          <div className="mx-auto max-w-6xl">
            <div className="mb-8">
              <h2 className="text-3xl font-bold text-white">Dashboard</h2>
              <p className="text-slate-400">System status and quick actions</p>
            </div>

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              <QuickStats />
              <ProactiveAlerts />
              <DashboardPreflight />
              <DashboardSettings />
              <DashboardQuickActions />
              <SystemStats />
              <SigmaMiniGallery />
              <RiskScoring />
            </div>
          </div>
        </main>
      </div>
    </ProtectedRoute>
  );
}
