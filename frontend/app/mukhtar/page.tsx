'use client';

import { useCallback, useEffect, useState } from 'react';

import { api, ApiError } from '../../lib/api';
import type {
  ChangeRequestStatus,
  ChangeRequestType,
  Household,
  HouseholdVerificationStatus,
  PopulationChangeRequest,
} from '../../lib/types';

const REQUEST_TYPE_LABELS: Record<ChangeRequestType, string> = {
  birth: 'ولادة',
  death: 'وفاة',
  address_change: 'تغيير عنوان',
  correction: 'تصحيح بيانات',
  add_member: 'إضافة فرد',
  remove_member: 'إزالة فرد',
};

const STATUS_LABELS: Record<ChangeRequestStatus, string> = {
  submitted: 'مُرسل',
  mukhtar_review: 'بانتظار المختار',
  municipality_review: 'بانتظار البلدية',
  approved: 'مُعتمد',
  rejected: 'مرفوض',
};

const VERIFICATION_LABELS: Record<HouseholdVerificationStatus, string> = {
  pending: 'بانتظار التحقق',
  verified: 'موثّقة',
  rejected: 'مرفوضة',
};

export default function MukhtarPage() {
  const [households, setHouseholds] = useState<Household[]>([]);
  const [pending, setPending] = useState<PopulationChangeRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [hh, prs] = await Promise.all([
        api.listHouseholds({}),
        api.listChangeRequests({ status: 'mukhtar_review' }),
      ]);
      setHouseholds(hh);
      setPending(prs);
    } catch (err) {
      if (err instanceof ApiError && err.status === 403) {
        setError('لا تملك صلاحية الوصول إلى صفحة المختار.');
      } else if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('تعذّر تحميل بيانات المختار.');
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    reload();
  }, [reload]);

  const decide = async (id: number, approve: boolean) => {
    setBusyId(id);
    try {
      await api.mukhtarDecision(id, { approve });
      await reload();
    } catch (err) {
      if (err instanceof ApiError) setError(err.message);
      else setError('تعذّر إرسال القرار.');
    } finally {
      setBusyId(null);
    }
  };

  const verify = async (
    id: number,
    status: 'verified' | 'rejected' | 'pending',
  ) => {
    setBusyId(id);
    try {
      await api.updateHouseholdVerification(id, status);
      await reload();
    } catch (err) {
      if (err instanceof ApiError) setError(err.message);
      else setError('تعذّر تحديث حالة الأسرة.');
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-gov-dark">صفحة المختار</h1>
        <p className="mt-1 text-sm text-slate-600">
          مراجعة طلبات التغيير السكاني والتحقق من الأسر ضمن نطاقك. الصلاحيات تُحقَّق
          في الواجهة الخلفية.
        </p>
      </header>

      {error && (
        <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
          {error}
        </div>
      )}

      <section className="card">
        <h2 className="text-lg font-bold text-gov-dark">طلبات بانتظار مراجعتك</h2>
        {loading ? (
          <p className="mt-2 text-sm text-slate-500">جاري التحميل...</p>
        ) : pending.length === 0 ? (
          <p className="mt-2 text-sm text-slate-500">لا توجد طلبات بانتظار المراجعة.</p>
        ) : (
          <ul className="mt-3 divide-y divide-slate-100">
            {pending.map((req) => (
              <li key={req.id} className="space-y-2 py-3">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold text-slate-700">
                      طلب #{req.id} — {REQUEST_TYPE_LABELS[req.request_type]}
                    </p>
                    <p className="text-xs text-slate-500">
                      الأسرة #{req.household_id}
                      {req.target_person_id ? ` — الشخص #${req.target_person_id}` : ''}
                    </p>
                    {req.reason && (
                      <p className="mt-1 text-xs text-slate-600">السبب: {req.reason}</p>
                    )}
                  </div>
                  <span className="rounded-md bg-amber-50 px-2 py-1 text-xs text-amber-700">
                    {STATUS_LABELS[req.status]}
                  </span>
                </div>
                <details className="text-xs text-slate-600">
                  <summary className="cursor-pointer text-slate-500 hover:text-slate-700">
                    تفاصيل الطلب
                  </summary>
                  <pre dir="ltr" className="mt-2 overflow-x-auto rounded bg-slate-50 p-2">
                    {JSON.stringify(req.payload, null, 2)}
                  </pre>
                </details>
                <div className="flex gap-2">
                  <button
                    type="button"
                    className="btn-primary"
                    disabled={busyId === req.id}
                    onClick={() => decide(req.id, true)}
                  >
                    موافقة
                  </button>
                  <button
                    type="button"
                    className="btn-secondary"
                    disabled={busyId === req.id}
                    onClick={() => decide(req.id, false)}
                  >
                    رفض
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="card">
        <h2 className="text-lg font-bold text-gov-dark">الأسر ضمن نطاقك</h2>
        {loading ? (
          <p className="mt-2 text-sm text-slate-500">جاري التحميل...</p>
        ) : households.length === 0 ? (
          <p className="mt-2 text-sm text-slate-500">لا توجد أسر مرتبطة بنطاقك.</p>
        ) : (
          <div className="mt-3 overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500">
                  <th className="px-3 py-2 text-right">رمز الأسرة</th>
                  <th className="px-3 py-2 text-right">العنوان</th>
                  <th className="px-3 py-2 text-right">التوثيق</th>
                  <th className="px-3 py-2 text-right">إجراءات</th>
                </tr>
              </thead>
              <tbody>
                {households.map((h) => (
                  <tr key={h.id} className="border-b border-slate-100">
                    <td className="px-3 py-2 font-mono text-xs text-slate-700">
                      {h.code}
                    </td>
                    <td className="px-3 py-2 text-slate-700">{h.address_line}</td>
                    <td className="px-3 py-2">
                      <span
                        className={`rounded-md px-2 py-1 text-xs ${
                          h.verification_status === 'verified'
                            ? 'bg-emerald-50 text-emerald-700'
                            : h.verification_status === 'pending'
                            ? 'bg-amber-50 text-amber-700'
                            : 'bg-rose-50 text-rose-700'
                        }`}
                      >
                        {VERIFICATION_LABELS[h.verification_status]}
                      </span>
                    </td>
                    <td className="px-3 py-2">
                      <div className="flex gap-2">
                        <button
                          type="button"
                          className="btn-primary"
                          disabled={busyId === h.id || h.verification_status === 'verified'}
                          onClick={() => verify(h.id, 'verified')}
                        >
                          توثيق
                        </button>
                        <button
                          type="button"
                          className="btn-secondary"
                          disabled={busyId === h.id || h.verification_status === 'rejected'}
                          onClick={() => verify(h.id, 'rejected')}
                        >
                          رفض
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
