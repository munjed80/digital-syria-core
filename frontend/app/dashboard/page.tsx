'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

import StatusBadge from '../../components/StatusBadge';
import { api, ApiError } from '../../lib/api';
import { useAuth } from '../../lib/auth-context';
import { formatDateAr } from '../../lib/services-meta';
import type { ServiceRequest } from '../../lib/types';

export default function DashboardPage() {
  const { user } = useAuth();
  const [requests, setRequests] = useState<ServiceRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api
      .listRequests()
      .then((data) => {
        if (!cancelled) setRequests(data);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof ApiError ? err.message : 'تعذّر تحميل البيانات.');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const total = requests.length;
  const open = requests.filter(
    (r) => r.current_status !== 'resolved' && r.current_status !== 'rejected',
  ).length;
  const resolved = requests.filter((r) => r.current_status === 'resolved').length;

  const recent = requests.slice(0, 5);

  return (
    <div className="space-y-8">
      <section>
        <h1 className="text-2xl font-bold text-gov-dark">
          مرحباً، {user?.full_name}
        </h1>
        <p className="mt-1 text-sm text-slate-600">
          لوحة المواطن الرئيسية لإدارة طلباتك ومتابعة حالتها.
        </p>
      </section>

      <section className="grid gap-4 sm:grid-cols-3">
        <div className="card">
          <p className="text-sm text-slate-500">إجمالي الطلبات</p>
          <p className="mt-2 text-3xl font-bold text-gov-dark">{total}</p>
        </div>
        <div className="card">
          <p className="text-sm text-slate-500">طلبات مفتوحة</p>
          <p className="mt-2 text-3xl font-bold text-amber-600">{open}</p>
        </div>
        <div className="card">
          <p className="text-sm text-slate-500">طلبات مكتملة</p>
          <p className="mt-2 text-3xl font-bold text-emerald-600">{resolved}</p>
        </div>
      </section>

      <section className="card">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-bold text-gov-dark">آخر الطلبات</h2>
          <Link href="/requests" className="text-sm font-medium text-gov hover:underline">
            عرض كل الطلبات ←
          </Link>
        </div>

        {loading ? (
          <p className="text-sm text-slate-500">جاري التحميل...</p>
        ) : error ? (
          <p className="text-sm text-rose-600">{error}</p>
        ) : recent.length === 0 ? (
          <div className="rounded-md border border-dashed border-slate-300 p-6 text-center">
            <p className="text-sm text-slate-600">
              لا توجد طلبات بعد.{' '}
              <Link href="/services" className="font-semibold text-gov hover:underline">
                تصفّح كتالوج الخدمات
              </Link>{' '}
              لتقديم طلبك الأول.
            </p>
          </div>
        ) : (
          <ul className="divide-y divide-slate-200">
            {recent.map((request) => (
              <li key={request.id} className="flex items-center justify-between py-3">
                <div>
                  <Link
                    href={`/requests/${request.id}`}
                    className="text-sm font-semibold text-slate-800 hover:text-gov"
                  >
                    {request.title}
                  </Link>
                  <p className="mt-1 text-xs text-slate-500">
                    رقم الطلب #{request.id} • {formatDateAr(request.created_at)}
                  </p>
                </div>
                <StatusBadge status={request.current_status} />
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="card bg-gov-light">
        <h2 className="text-lg font-bold text-gov-dark">جاهز لتقديم طلب جديد؟</h2>
        <p className="mt-1 text-sm text-slate-700">
          استعرض الخدمات المتوفرة وقدم طلبك الإلكتروني خلال دقائق.
        </p>
        <div className="mt-4">
          <Link href="/services" className="btn-primary">
            تصفح الخدمات
          </Link>
        </div>
      </section>
    </div>
  );
}
