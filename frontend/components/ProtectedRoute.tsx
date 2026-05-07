'use client';

import { useRouter } from 'next/navigation';
import { ReactNode, useEffect } from 'react';

import { useAuth } from '../lib/auth-context';
import type { UserRole } from '../lib/types';

interface ProtectedRouteProps {
  children: ReactNode;
  /**
   * Optional whitelist of roles allowed to view the wrapped subtree. If
   * omitted, any authenticated user is allowed. Role enforcement here is a UX
   * convenience only — the backend remains the source of truth for
   * authorization.
   */
  allowedRoles?: UserRole[];
}

export default function ProtectedRoute({
  children,
  allowedRoles,
}: ProtectedRouteProps) {
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

  if (allowedRoles && allowedRoles.length > 0 && !allowedRoles.includes(user.role)) {
    return (
      <div className="mx-auto mt-12 max-w-xl rounded-md border border-rose-200 bg-rose-50 p-6 text-center">
        <h2 className="text-lg font-bold text-rose-800">لا تملك صلاحية الوصول</h2>
        <p className="mt-2 text-sm text-rose-700">
          هذه الصفحة مخصّصة للموظفين أو المشرفين أو المسؤولين. إذا كنت تعتقد أن
          هذا خطأ، يُرجى التواصل مع الجهة المختصة.
        </p>
        <p className="mt-3 text-xs text-rose-600">
          ملاحظة: التحقق النهائي من الصلاحيات يتمّ في الواجهة الخلفية.
        </p>
      </div>
    );
  }

  return <>{children}</>;
}
