'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';

import StatusBadge from '../../components/StatusBadge';
import { api, ApiError } from '../../lib/api';
import { formatDateAr, STATUS_LABELS_AR } from '../../lib/services-meta';
import type { RequestStatus, ServiceItem, ServiceRequest } from '../../lib/types';

type StatusFilter = 'all' | RequestStatus;

export default function RequestsPage() {
  const [requests, setRequests] = useState<ServiceRequest[]>([]);
  const [services, setServices] = useState<ServiceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    Promise.all([api.listRequests(), api.listServices()])
      .then(([reqs, srv]) => {
        if (cancelled) return;
        setRequests(reqs);
        setServices(srv);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof ApiError ? err.message : 'تعذّر تحميل الطلبات.');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const serviceMap = useMemo(() => {
    const map = new Map<number, ServiceItem>();
    for (const s of services) map.set(s.id, s);
    return map;
  }, [services]);

  const filtered = useMemo(() => {
    if (statusFilter === 'all') return requests;
    return requests.filter((r) => r.current_status === statusFilter);
  }, [requests, statusFilter]);

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gov-dark">طلباتي</h1>
          <p className="mt-1 text-sm text-slate-600">
            عرض جميع الطلبات التي قمت بتقديمها وحالتها الحالية.
          </p>
        </div>
        <Link href="/services" className="btn-primary self-start sm:self-auto">
          تقديم طلب جديد
        </Link>
      </header>

      <div className="card">
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <label htmlFor="status_filter" className="text-sm font-medium text-slate-700">
            تصفية حسب الحالة:
          </label>
          <select
            id="status_filter"
            className="form-input mt-0 w-auto"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
          >
            <option value="all">الكل</option>
            {(Object.keys(STATUS_LABELS_AR) as RequestStatus[]).map((status) => (
              <option key={status} value={status}>
                {STATUS_LABELS_AR[status]}
              </option>
            ))}
          </select>
        </div>

        {loading ? (
          <p className="text-sm text-slate-500">جاري تحميل الطلبات...</p>
        ) : error ? (
          <div className="rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {error}
          </div>
        ) : filtered.length === 0 ? (
          <div className="rounded-md border border-dashed border-slate-300 p-6 text-center text-sm text-slate-600">
            لا توجد طلبات مطابقة.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-right text-sm">
              <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500">
                <tr>
                  <th scope="col" className="px-4 py-3">
                    رقم الطلب
                  </th>
                  <th scope="col" className="px-4 py-3">
                    الخدمة
                  </th>
                  <th scope="col" className="px-4 py-3">
                    عنوان الطلب
                  </th>
                  <th scope="col" className="px-4 py-3">
                    الحالة
                  </th>
                  <th scope="col" className="px-4 py-3">
                    تاريخ التقديم
                  </th>
                  <th scope="col" className="px-4 py-3">
                    الإجراء
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 bg-white">
                {filtered.map((request) => {
                  const service = serviceMap.get(request.service_id);
                  return (
                    <tr key={request.id}>
                      <td className="whitespace-nowrap px-4 py-3 font-mono text-xs text-slate-500">
                        #{request.id}
                      </td>
                      <td className="px-4 py-3 text-slate-700">
                        {service?.title_ar || `خدمة #${request.service_id}`}
                      </td>
                      <td className="px-4 py-3 text-slate-800">{request.title}</td>
                      <td className="px-4 py-3">
                        <StatusBadge status={request.current_status} />
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-slate-500">
                        {formatDateAr(request.created_at)}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3">
                        <Link
                          href={`/requests/${request.id}`}
                          className="text-sm font-semibold text-gov hover:underline"
                        >
                          عرض التفاصيل
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
