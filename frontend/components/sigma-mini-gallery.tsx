'use client';

import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

const SIGMA_RULES = [
  {
    name: 'Failed Logins 24h',
    description: 'Recent authentication failures',
    query: 'failed login attempts',
  },
  {
    name: 'RDP 24h',
    description: 'Remote desktop protocol usage',
    query: 'RDP connections',
  },
  {
    name: '/etc/shadow Access',
    description: 'Suspicious file access',
    query: 'etc shadow file access',
  },
];

export function SigmaMiniGallery() {
  const router = useRouter();

  const handleSelectRule = (query: string) => {
    // Store the query and navigate to chat with it pre-filled
    router.push(`/chat?query=${encodeURIComponent(query)}`);
  };

  return (
    <Card className="border-slate-700 bg-slate-900/50 p-6">
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold text-white">Sigma Mini Gallery</h3>
          <p className="text-sm text-slate-400">Common threat detection rules</p>
        </div>

        <div className="space-y-2">
          {SIGMA_RULES.map((rule) => (
            <div key={rule.name} className="space-y-2">
              <div className="flex items-center justify-between rounded-md border border-slate-700 bg-slate-800/30 p-3">
                <div className="flex-1">
                  <div className="font-medium text-slate-200">{rule.name}</div>
                  <div className="text-xs text-slate-500">{rule.description}</div>
                </div>
              </div>
              <Button
                size="sm"
                onClick={() => handleSelectRule(rule.query)}
                className="w-full bg-cyan-600 hover:bg-cyan-700"
              >
                Load Rule
              </Button>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
}
