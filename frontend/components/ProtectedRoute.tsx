'use client';

import { useRouter } from 'next/navigation';
import { ReactNode, useEffect } from 'react';

import { useAuth } from '../lib/auth-context';

interface ProtectedRouteProps {
  children: ReactNode;
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { user, token, initializing } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!initializing && !token) {
      router.replace('/login');
    }
  }, [initializing, token, router]);

  if (initializing) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center text-slate-500">
        جاري التحميل...
      </div>
    );
  }

  if (!token || !user) {
    return null;
  }

  return <>{children}</>;
}
