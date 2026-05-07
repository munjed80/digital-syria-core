'use client';

import { useEffect, useState } from 'react';

import { api, ApiError } from '../../lib/api';

interface Counts {
  servicesCount: number | null;
  requestsCount: number | null;
}

export default function AdminFoundationPage() {
  const [counts, setCounts] = useState<Counts>({
    servicesCount: null,
    requestsCount: null,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    Promise.all([api.listServices(), api.dashboardSummary()])
      .then(([services, summary]) => {
        if (cancelled) return;
        setCounts({
          servicesCount: services.length,
          requestsCount: summary.total_requests,
        });
      })
      .catch((err) => {
        if (cancelled) return;
        if (err instanceof ApiError) {
          if (err.status === 403) {
            setError(
              'لا تملك صلاحية الوصول إلى لوحة المسؤول. يجب أن يكون حسابك بدور مسؤول.',
            );
          } else {
            setError(err.message);
          }
        } else {
          setError('تعذّر تحميل بيانات لوحة المسؤول.');
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-gov-dark">لوحة المسؤول</h1>
        <p className="mt-1 text-sm text-slate-600">
          نظرة عامة على المنصة. هذه نسخة أساسية مخصّصة لمرحلة الـ MVP وليست
          الكونسول الإداري الكامل.
        </p>
      </header>

      <section className="rounded-md border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        <p className="font-semibold">ملاحظة</p>
        <p className="mt-1 leading-6">
          هذه الصفحة هي <strong>أساس لوحة المسؤول</strong> ضمن مرحلة الـ MVP.
          لم تُبنَ بعد كامل الميزات الإدارية (إدارة المستخدمين، الأدوار،
          إعدادات الخدمات، التقارير المتقدّمة، إعدادات النظام). يتمّ التحقق
          النهائي من جميع الصلاحيات في الواجهة الخلفية.
        </p>
      </section>

      {error && (
        <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
          {error}
        </div>
      )}

      <section className="grid gap-4 sm:grid-cols-3">
        <div className="card">
          <p className="text-sm text-slate-500">عدد الخدمات</p>
          <p className="mt-2 text-3xl font-bold text-gov-dark">
            {loading ? '…' : counts.servicesCount ?? '—'}
          </p>
        </div>
        <div className="card">
          <p className="text-sm text-slate-500">عدد الطلبات</p>
          <p className="mt-2 text-3xl font-bold text-gov-dark">
            {loading ? '…' : counts.requestsCount ?? '—'}
          </p>
        </div>
        <div className="card">
          <p className="text-sm text-slate-500">المستخدمون</p>
          <p className="mt-2 text-3xl font-bold text-slate-400">—</p>
          <p className="mt-1 text-xs text-slate-500">
            (مكان مخصّص — لم يُربط بعد بواجهة خلفية لإدارة المستخدمين)
          </p>
        </div>
      </section>

      <section className="card">
        <h2 className="text-lg font-bold text-gov-dark">سجلات التدقيق</h2>
        <p className="mt-1 text-sm text-slate-600">
          واجهة عرض سجلات التدقيق ستُضاف لاحقاً. يمكن للمسؤولين حالياً قراءة
          السجلات عبر الواجهة الخلفية على المسار التالي:
        </p>
        <p className="mt-2 font-mono text-xs text-slate-700">
          GET /api/v1/audit-logs
        </p>
        <button
          type="button"
          disabled
          className="btn-secondary mt-4 cursor-not-allowed opacity-60"
          aria-disabled="true"
          title="سيتم تفعيل هذه الواجهة في مرحلة لاحقة"
        >
          فتح سجلات التدقيق (قريباً)
        </button>
      </section>
    </div>
  );
}
