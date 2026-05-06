'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';

import StatusBadge from '../../../components/StatusBadge';
import { api, ApiError } from '../../../lib/api';
import { formatDateAr, STATUS_LABELS_AR } from '../../../lib/services-meta';
import type { ServiceItem, ServiceRequestDetail } from '../../../lib/types';

export default function RequestDetailPage() {
  const params = useParams<{ id: string }>();
  const requestId = Number(params?.id);

  const [request, setRequest] = useState<ServiceRequestDetail | null>(null);
  const [service, setService] = useState<ServiceItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!Number.isFinite(requestId)) {
      setError('معرّف الطلب غير صالح.');
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    api
      .getRequest(requestId)
      .then(async (data) => {
        if (cancelled) return;
        setRequest(data);
        try {
          const services = await api.listServices();
          if (cancelled) return;
          setService(services.find((s) => s.id === data.service_id) || null);
        } catch {
          /* service lookup is best-effort */
        }
      })
      .catch((err) => {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 404) {
          setError('الطلب غير موجود أو ليس لديك صلاحية الوصول إليه.');
        } else {
          setError(err instanceof ApiError ? err.message : 'تعذّر تحميل الطلب.');
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [requestId]);

  if (loading) {
    return <p className="text-sm text-slate-500">جاري تحميل الطلب...</p>;
  }

  if (error || !request) {
    return (
      <div className="card">
        <p className="text-sm text-rose-600">{error || 'الطلب غير متاح.'}</p>
        <div className="mt-4">
          <Link href="/requests" className="btn-secondary">
            العودة إلى طلباتي
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <nav className="text-sm text-slate-500">
        <Link href="/requests" className="hover:text-gov">
          طلباتي
        </Link>{' '}
        / <span className="text-slate-700">طلب رقم #{request.id}</span>
      </nav>

      <header className="card">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs font-mono text-slate-400">رقم التتبع</p>
            <h1 className="mt-1 text-2xl font-bold text-gov-dark">#{request.id}</h1>
            <p className="mt-2 text-base font-semibold text-slate-800">{request.title}</p>
            {service && (
              <p className="mt-1 text-sm text-slate-500">
                الخدمة: {service.title_ar}{' '}
                <span className="font-mono text-xs text-slate-400">
                  ({service.code})
                </span>
              </p>
            )}
          </div>
          <div className="text-left">
            <StatusBadge status={request.current_status} />
            <p className="mt-2 text-xs text-slate-500">
              تاريخ التقديم: {formatDateAr(request.created_at)}
            </p>
            <p className="text-xs text-slate-500">
              آخر تحديث: {formatDateAr(request.updated_at)}
            </p>
          </div>
        </div>
      </header>

      <section className="card">
        <h2 className="mb-3 text-lg font-bold text-gov-dark">تفاصيل الطلب</h2>
        <p className="whitespace-pre-line text-sm leading-7 text-slate-700">
          {request.description}
        </p>
      </section>

      <section className="card">
        <h2 className="mb-4 text-lg font-bold text-gov-dark">سجل الحالات</h2>
        {request.status_history.length === 0 ? (
          <p className="text-sm text-slate-500">لا يوجد سجل حالات بعد.</p>
        ) : (
          <ol className="relative space-y-6 border-r border-slate-200 pr-6">
            {request.status_history.map((entry) => (
              <li key={entry.id} className="relative">
                <span className="absolute -right-[1.6rem] top-1 h-3 w-3 rounded-full bg-gov" />
                <div className="flex flex-wrap items-center gap-2">
                  <StatusBadge status={entry.new_status} />
                  {entry.old_status !== entry.new_status && (
                    <span className="text-xs text-slate-500">
                      من «{STATUS_LABELS_AR[entry.old_status]}» إلى «
                      {STATUS_LABELS_AR[entry.new_status]}»
                    </span>
                  )}
                </div>
                <p className="mt-1 text-xs text-slate-500">
                  {formatDateAr(entry.created_at)}
                </p>
                {entry.comment && (
                  <p className="mt-2 rounded-md bg-slate-50 p-3 text-sm leading-6 text-slate-700">
                    {entry.comment}
                  </p>
                )}
              </li>
            ))}
          </ol>
        )}
      </section>

      {request.internal_notes.length > 0 && (
        <section className="card">
          <h2 className="mb-3 text-lg font-bold text-gov-dark">ملاحظات داخلية</h2>
          <ul className="space-y-3">
            {request.internal_notes.map((note) => (
              <li
                key={note.id}
                className="rounded-md border border-slate-200 bg-slate-50 p-3 text-sm leading-6 text-slate-700"
              >
                <p>{note.note}</p>
                <p className="mt-1 text-xs text-slate-500">
                  {formatDateAr(note.created_at)}
                </p>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
