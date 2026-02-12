'use client';

import React from "react"

import { useAppStore } from '@/lib/store';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const [mounted, setMounted] = useState(false);
  const isAuthenticated = useAppStore((state) => state.isAuthenticated);
  const router = useRouter();

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (mounted && !isAuthenticated()) {
      router.push('/login');
    }
  }, [mounted, isAuthenticated, router]);

  if (!mounted || !isAuthenticated()) {
    return null;
  }

  return <>{children}</>;
}
