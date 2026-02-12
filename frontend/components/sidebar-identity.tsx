'use client';

import { useAppStore } from '@/lib/store';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';

export function SidebarIdentity() {
  const user = useAppStore((state) => state.user);
  const logout = useAppStore((state) => state.logout);
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  if (!user) return null;

  return (
    <div className="space-y-2 border-b border-slate-700 pb-4">
      <div className="text-sm font-semibold text-slate-200">
        {user.username}
      </div>
      <div className="flex gap-2">
        <span className="inline-block rounded-full bg-cyan-500/20 px-2 py-1 text-xs font-medium text-cyan-400">
          {user.role}
        </span>
      </div>
      <Button
        variant="ghost"
        size="sm"
        onClick={handleLogout}
        className="w-full justify-start text-slate-400 hover:text-slate-200"
      >
        Logout
      </Button>
    </div>
  );
}
