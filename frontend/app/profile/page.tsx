'use client';

import { useRouter } from 'next/navigation';

import { useAuth } from '../../lib/auth-context';

const ROLE_LABELS: Record<string, string> = {
  citizen: 'مواطن',
  employee: 'موظف',
  supervisor: 'مشرف',
  admin: 'مدير النظام',
};

export default function ProfilePage() {
  const { user, logout } = useAuth();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  if (!user) return null;

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-gov-dark">الملف الشخصي</h1>
        <p className="mt-1 text-sm text-slate-600">
          معلومات حسابك في منصة سوريا الرقمية.
        </p>
      </header>

      <section className="card">
        <dl className="divide-y divide-slate-200">
          <div className="grid grid-cols-1 gap-1 py-3 sm:grid-cols-3">
            <dt className="text-sm font-medium text-slate-500">الاسم الكامل</dt>
            <dd className="sm:col-span-2 text-sm text-slate-800">{user.full_name}</dd>
          </div>
          <div className="grid grid-cols-1 gap-1 py-3 sm:grid-cols-3">
            <dt className="text-sm font-medium text-slate-500">البريد الإلكتروني</dt>
            <dd className="sm:col-span-2 text-sm text-slate-800" dir="ltr">
              {user.email}
            </dd>
          </div>
          <div className="grid grid-cols-1 gap-1 py-3 sm:grid-cols-3">
            <dt className="text-sm font-medium text-slate-500">الصلاحية</dt>
            <dd className="sm:col-span-2 text-sm text-slate-800">
              {ROLE_LABELS[user.role] || user.role}
            </dd>
          </div>
          <div className="grid grid-cols-1 gap-1 py-3 sm:grid-cols-3">
            <dt className="text-sm font-medium text-slate-500">معرّف الحساب</dt>
            <dd className="sm:col-span-2 font-mono text-sm text-slate-700">
              #{user.id}
            </dd>
          </div>
        </dl>
      </section>

      <section className="card">
        <h2 className="text-base font-bold text-gov-dark">إدارة الجلسة</h2>
        <p className="mt-1 text-sm text-slate-600">
          يمكنك إنهاء جلستك الحالية في أي وقت.
        </p>
        <div className="mt-4">
          <button type="button" className="btn-secondary" onClick={handleLogout}>
            تسجيل الخروج
          </button>
        </div>
      </section>
    </div>
  );
}
