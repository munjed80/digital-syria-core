'use client';

import { useEffect, useMemo, useState } from 'react';

import StatusBadge from '../../../components/StatusBadge';
import { api, ApiError } from '../../../lib/api';
import { formatDateAr, STATUS_LABELS_AR } from '../../../lib/services-meta';
import type {
  RequestStatus,
  ServiceRequest,
  ServiceRequestDetail,
} from '../../../lib/types';

const STATUS_OPTIONS: RequestStatus[] = [
  'submitted',
  'under_review',
  'in_progress',
  'resolved',
  'rejected',
];

export default function EmployeeRequestsPage() {
  const [requests, setRequests] = useState<ServiceRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [listError, setListError] = useState<string | null>(null);

  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detail, setDetail] = useState<ServiceRequestDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);

  const [statusValue, setStatusValue] = useState<RequestStatus>('submitted');
  const [statusComment, setStatusComment] = useState('');
  const [statusSaving, setStatusSaving] = useState(false);
  const [statusError, setStatusError] = useState<string | null>(null);
  const [statusSuccess, setStatusSuccess] = useState<string | null>(null);

  const [noteValue, setNoteValue] = useState('');
  const [noteSaving, setNoteSaving] = useState(false);
  const [noteError, setNoteError] = useState<string | null>(null);
  const [noteSuccess, setNoteSuccess] = useState<string | null>(null);

  const loadList = () => {
    setLoading(true);
    setListError(null);
    api
      .listRequests()
      .then((data) => setRequests(data))
      .catch((err) => {
        if (err instanceof ApiError) {
          if (err.status === 403) {
            setListError(
              'لا تملك صلاحية الوصول إلى قائمة الطلبات. يجب أن يكون حسابك بدور موظف أو مشرف أو مسؤول.',
            );
          } else {
            setListError(err.message);
          }
        } else {
          setListError('تعذّر تحميل قائمة الطلبات.');
        }
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadList();
  }, []);

  const loadDetail = (id: number) => {
    setSelectedId(id);
    setDetail(null);
    setDetailError(null);
    setStatusError(null);
    setStatusSuccess(null);
    setNoteError(null);
    setNoteSuccess(null);
    setNoteValue('');
    setDetailLoading(true);
    api
      .getRequest(id)
      .then((data) => {
        setDetail(data);
        setStatusValue(data.current_status);
        setStatusComment('');
      })
      .catch((err) => {
        if (err instanceof ApiError) {
          if (err.status === 403) {
            setDetailError('لا تملك صلاحية عرض هذا الطلب.');
          } else if (err.status === 404) {
            setDetailError('الطلب غير موجود.');
          } else {
            setDetailError(err.message);
          }
        } else {
          setDetailError('تعذّر تحميل تفاصيل الطلب.');
        }
      })
      .finally(() => setDetailLoading(false));
  };

  const submitStatus = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!detail) return;
    setStatusSaving(true);
    setStatusError(null);
    setStatusSuccess(null);
    try {
      const updated = await api.updateRequestStatus(detail.id, {
        new_status: statusValue,
        comment: statusComment.trim() ? statusComment.trim() : null,
      });
      setStatusSuccess('تم تحديث حالة الطلب بنجاح.');
      setStatusComment('');
      // Refresh detail and list to reflect the change.
      loadDetail(updated.id);
      loadList();
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 403) {
          setStatusError('لا تملك صلاحية تعديل حالة هذا الطلب.');
        } else {
          setStatusError(err.message);
        }
      } else {
        setStatusError('تعذّر تحديث الحالة.');
      }
    } finally {
      setStatusSaving(false);
    }
  };

  const submitNote = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!detail) return;
    const trimmed = noteValue.trim();
    if (!trimmed) {
      setNoteError('لا يمكن إضافة ملاحظة فارغة.');
      return;
    }
    setNoteSaving(true);
    setNoteError(null);
    setNoteSuccess(null);
    try {
      await api.addInternalNote(detail.id, trimmed);
      setNoteSuccess('تمت إضافة الملاحظة الداخلية.');
      setNoteValue('');
      loadDetail(detail.id);
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 403) {
          setNoteError('لا تملك صلاحية إضافة ملاحظات داخلية.');
        } else {
          setNoteError(err.message);
        }
      } else {
        setNoteError('تعذّر إضافة الملاحظة.');
      }
    } finally {
      setNoteSaving(false);
    }
  };

  const sortedRequests = useMemo(
    () => [...requests].sort((a, b) => b.id - a.id),
    [requests],
  );

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-gov-dark">طلبات المعالجة</h1>
        <p className="mt-1 text-sm text-slate-600">
          واجهة الموظفين لمراجعة الطلبات المقدّمة، تغيير حالتها، وإضافة ملاحظات
          داخلية. التحقق النهائي من الصلاحيات يتمّ في الواجهة الخلفية.
        </p>
      </header>

      <div className="grid gap-6 lg:grid-cols-5">
        <section className="card lg:col-span-2">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-bold text-gov-dark">الطلبات</h2>
            <button type="button" onClick={loadList} className="btn-secondary text-xs">
              تحديث
            </button>
          </div>

          {loading ? (
            <p className="text-sm text-slate-500">جاري التحميل...</p>
          ) : listError ? (
            <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
              {listError}
            </div>
          ) : sortedRequests.length === 0 ? (
            <p className="rounded-md border border-dashed border-slate-300 p-4 text-center text-sm text-slate-500">
              لا توجد طلبات حالياً.
            </p>
          ) : (
            <ul className="divide-y divide-slate-200">
              {sortedRequests.map((req) => {
                const isActive = selectedId === req.id;
                return (
                  <li key={req.id}>
                    <button
                      type="button"
                      onClick={() => loadDetail(req.id)}
                      className={`flex w-full flex-col gap-1 rounded-md px-3 py-3 text-right transition ${
                        isActive
                          ? 'bg-gov-light'
                          : 'hover:bg-slate-50'
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-sm font-semibold text-slate-800">
                          {req.title}
                        </span>
                        <StatusBadge status={req.current_status} />
                      </div>
                      <span className="text-xs text-slate-500">
                        #{req.id} • {formatDateAr(req.created_at)}
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </section>

        <section className="space-y-4 lg:col-span-3">
          {selectedId === null ? (
            <div className="card text-sm text-slate-500">
              اختر طلباً من القائمة لعرض التفاصيل.
            </div>
          ) : detailLoading ? (
            <div className="card text-sm text-slate-500">جاري تحميل تفاصيل الطلب...</div>
          ) : detailError ? (
            <div className="card">
              <p className="text-sm text-rose-700">{detailError}</p>
            </div>
          ) : detail ? (
            <>
              <div className="card">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-xs font-mono text-slate-400">رقم التتبع</p>
                    <h3 className="text-xl font-bold text-gov-dark">#{detail.id}</h3>
                    <p className="mt-1 text-base font-semibold text-slate-800">
                      {detail.title}
                    </p>
                  </div>
                  <StatusBadge status={detail.current_status} />
                </div>
                <p className="mt-3 whitespace-pre-line text-sm leading-7 text-slate-700">
                  {detail.description}
                </p>
                <p className="mt-3 text-xs text-slate-500">
                  تاريخ التقديم: {formatDateAr(detail.created_at)}
                </p>
              </div>

              <form onSubmit={submitStatus} className="card space-y-3">
                <h3 className="text-base font-bold text-gov-dark">تغيير الحالة</h3>
                <div>
                  <label htmlFor="emp_status" className="text-sm font-medium text-slate-700">
                    الحالة الجديدة
                  </label>
                  <select
                    id="emp_status"
                    className="form-input"
                    value={statusValue}
                    onChange={(e) => setStatusValue(e.target.value as RequestStatus)}
                  >
                    {STATUS_OPTIONS.map((s) => (
                      <option key={s} value={s}>
                        {STATUS_LABELS_AR[s]}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label htmlFor="emp_comment" className="text-sm font-medium text-slate-700">
                    ملاحظة (اختيارية، تظهر في سجل الحالات)
                  </label>
                  <textarea
                    id="emp_comment"
                    className="form-input"
                    rows={2}
                    value={statusComment}
                    onChange={(e) => setStatusComment(e.target.value)}
                  />
                </div>
                {statusError && (
                  <div className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
                    {statusError}
                  </div>
                )}
                {statusSuccess && (
                  <div className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
                    {statusSuccess}
                  </div>
                )}
                <button
                  type="submit"
                  disabled={statusSaving}
                  className="btn-primary disabled:opacity-60"
                >
                  {statusSaving ? 'جاري الحفظ...' : 'حفظ الحالة'}
                </button>
              </form>

              <form onSubmit={submitNote} className="card space-y-3">
                <h3 className="text-base font-bold text-gov-dark">إضافة ملاحظة داخلية</h3>
                <p className="text-xs text-slate-500">
                  لا تظهر الملاحظات الداخلية للمواطن. تُستخدم للتنسيق بين الموظفين.
                </p>
                <textarea
                  className="form-input"
                  rows={3}
                  value={noteValue}
                  onChange={(e) => setNoteValue(e.target.value)}
                  placeholder="اكتب الملاحظة هنا..."
                />
                {noteError && (
                  <div className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
                    {noteError}
                  </div>
                )}
                {noteSuccess && (
                  <div className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
                    {noteSuccess}
                  </div>
                )}
                <button
                  type="submit"
                  disabled={noteSaving}
                  className="btn-primary disabled:opacity-60"
                >
                  {noteSaving ? 'جاري الإضافة...' : 'إضافة الملاحظة'}
                </button>
              </form>

              <div className="card">
                <h3 className="mb-3 text-base font-bold text-gov-dark">سجل الحالات</h3>
                {detail.status_history.length === 0 ? (
                  <p className="text-sm text-slate-500">لا يوجد سجل حالات بعد.</p>
                ) : (
                  <ul className="space-y-3">
                    {detail.status_history.map((h) => (
                      <li
                        key={h.id}
                        className="rounded-md border border-slate-200 p-3 text-sm text-slate-700"
                      >
                        <div className="flex items-center gap-2">
                          <StatusBadge status={h.new_status} />
                          {h.old_status !== h.new_status && (
                            <span className="text-xs text-slate-500">
                              من «{STATUS_LABELS_AR[h.old_status]}» إلى «
                              {STATUS_LABELS_AR[h.new_status]}»
                            </span>
                          )}
                        </div>
                        <p className="mt-1 text-xs text-slate-500">
                          {formatDateAr(h.created_at)}
                        </p>
                        {h.comment && (
                          <p className="mt-2 text-sm leading-6 text-slate-700">
                            {h.comment}
                          </p>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              {detail.internal_notes.length > 0 && (
                <div className="card">
                  <h3 className="mb-3 text-base font-bold text-gov-dark">
                    الملاحظات الداخلية
                  </h3>
                  <ul className="space-y-2">
                    {detail.internal_notes.map((n) => (
                      <li
                        key={n.id}
                        className="rounded-md bg-slate-50 p-3 text-sm leading-6 text-slate-700"
                      >
                        <p>{n.note}</p>
                        <p className="mt-1 text-xs text-slate-500">
                          {formatDateAr(n.created_at)}
                        </p>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          ) : null}
        </section>
      </div>
    </div>
  );
}
