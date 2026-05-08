'use client';

import { useCallback, useEffect, useState } from 'react';

import { api, ApiError } from '../../../lib/api';
import type {
  ChangeRequestType,
  Gender,
  HouseholdDetail,
  PopulationChangeRequest,
  RelationToHead,
} from '../../../lib/types';

const RELATION_LABELS: Record<RelationToHead, string> = {
  self: 'رب الأسرة',
  spouse: 'الزوج/الزوجة',
  child: 'ابن/ابنة',
  parent: 'والد/والدة',
  sibling: 'أخ/أخت',
  other: 'أخرى',
};

const GENDER_LABELS: Record<Gender, string> = {
  male: 'ذكر',
  female: 'أنثى',
};

const REQUEST_TYPE_LABELS: Record<ChangeRequestType, string> = {
  birth: 'تسجيل ولادة',
  death: 'تسجيل وفاة',
  address_change: 'تغيير عنوان',
  correction: 'تصحيح بيانات',
  add_member: 'إضافة فرد',
  remove_member: 'إزالة فرد',
};

const STATUS_LABELS: Record<string, string> = {
  submitted: 'مُرسل',
  mukhtar_review: 'بانتظار المختار',
  municipality_review: 'بانتظار البلدية',
  approved: 'مُعتمد',
  rejected: 'مرفوض',
};

export default function FamilyProfilePage() {
  const [household, setHousehold] = useState<HouseholdDetail | null>(null);
  const [requests, setRequests] = useState<PopulationChangeRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Form state for new birth registration
  const [requestType, setRequestType] = useState<ChangeRequestType>('birth');
  const [fullName, setFullName] = useState('');
  const [birthDate, setBirthDate] = useState('');
  const [gender, setGender] = useState<Gender>('male');
  const [relation, setRelation] = useState<RelationToHead>('child');
  const [reason, setReason] = useState('');
  const [newAddress, setNewAddress] = useState('');
  const [targetPersonId, setTargetPersonId] = useState<string>('');

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [households, reqs] = await Promise.all([
        api.listHouseholds({}),
        api.listChangeRequests({}),
      ]);
      if (households.length === 0) {
        setHousehold(null);
      } else {
        const detail = await api.getHousehold(households[0].id);
        setHousehold(detail);
      }
      setRequests(reqs);
    } catch (err) {
      if (err instanceof ApiError && err.status === 403) {
        setError('لا تملك صلاحية الوصول إلى ملف الأسرة.');
      } else if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('تعذّر تحميل ملف الأسرة.');
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    reload();
  }, [reload]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!household) return;
    setSubmitting(true);
    setInfo(null);
    setError(null);
    try {
      const payload: Record<string, unknown> = {};
      if (requestType === 'birth' || requestType === 'add_member') {
        payload.full_name = fullName;
        payload.gender = gender;
        payload.relation_to_head = relation;
        if (birthDate) payload.birth_date = birthDate;
      } else if (requestType === 'address_change') {
        payload.address_line = newAddress;
      } else if (requestType === 'death') {
        // target_person_id sent at top level
      } else if (requestType === 'correction') {
        if (fullName) payload.full_name = fullName;
        if (birthDate) payload.birth_date = birthDate;
      }

      const targetId = targetPersonId ? Number(targetPersonId) : undefined;
      await api.submitChangeRequest({
        request_type: requestType,
        household_id: household.id,
        target_person_id: targetId ?? null,
        payload,
        reason: reason || null,
      });
      setInfo('تم إرسال الطلب بنجاح. سيتم مراجعته من قبل المختار.');
      setFullName('');
      setBirthDate('');
      setReason('');
      setNewAddress('');
      setTargetPersonId('');
      await reload();
    } catch (err) {
      if (err instanceof ApiError) setError(err.message);
      else setError('تعذّر إرسال الطلب.');
    } finally {
      setSubmitting(false);
    }
  };

  const needsTarget =
    requestType === 'death' ||
    requestType === 'remove_member' ||
    requestType === 'correction';

  const needsPerson =
    requestType === 'birth' ||
    requestType === 'add_member' ||
    requestType === 'correction';

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-gov-dark">ملف الأسرة</h1>
        <p className="mt-1 text-sm text-slate-600">
          عرض بيانات أسرتك وتقديم طلبات التغيير الرسمية. لا يمكن تعديل بيانات
          السجل المدني مباشرةً — يجب إرسال طلب يُراجَع من قبل المختار وعند الحاجة
          من رئيس البلدية.
        </p>
      </header>

      {error && (
        <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
          {error}
        </div>
      )}
      {info && (
        <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">
          {info}
        </div>
      )}

      {loading ? (
        <p className="text-sm text-slate-500">جاري التحميل...</p>
      ) : !household ? (
        <div className="card">
          <p className="text-sm text-slate-600">
            لا توجد أسرة مسجّلة باسمك حالياً. يرجى التواصل مع المختار في منطقتك
            لإنشاء سجل الأسرة.
          </p>
        </div>
      ) : (
        <>
          <section className="card">
            <h2 className="text-lg font-bold text-gov-dark">بيانات الأسرة</h2>
            <dl className="mt-3 grid gap-3 sm:grid-cols-2 text-sm">
              <div>
                <dt className="text-slate-500">رمز الأسرة</dt>
                <dd className="font-mono text-slate-800">{household.code}</dd>
              </div>
              <div>
                <dt className="text-slate-500">العنوان</dt>
                <dd className="text-slate-800">{household.address_line}</dd>
              </div>
              <div>
                <dt className="text-slate-500">حالة التوثيق</dt>
                <dd className="text-slate-800">
                  {household.verification_status === 'verified'
                    ? 'موثّقة'
                    : household.verification_status === 'pending'
                    ? 'بانتظار التحقق'
                    : 'مرفوضة'}
                </dd>
              </div>
            </dl>
          </section>

          <section className="card">
            <h2 className="text-lg font-bold text-gov-dark">أفراد الأسرة</h2>
            {household.members.length === 0 ? (
              <p className="mt-2 text-sm text-slate-500">لا يوجد أفراد مسجّلون.</p>
            ) : (
              <div className="mt-3 overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-200 text-slate-500">
                      <th className="px-3 py-2 text-right">الاسم</th>
                      <th className="px-3 py-2 text-right">الصلة</th>
                      <th className="px-3 py-2 text-right">الجنس</th>
                      <th className="px-3 py-2 text-right">تاريخ الميلاد</th>
                      <th className="px-3 py-2 text-right">الحالة</th>
                    </tr>
                  </thead>
                  <tbody>
                    {household.members.map((m) => (
                      <tr key={m.id} className="border-b border-slate-100">
                        <td className="px-3 py-2 text-slate-800">{m.full_name}</td>
                        <td className="px-3 py-2">{RELATION_LABELS[m.relation_to_head]}</td>
                        <td className="px-3 py-2">{GENDER_LABELS[m.gender]}</td>
                        <td className="px-3 py-2">{m.birth_date ?? '—'}</td>
                        <td className="px-3 py-2">
                          {m.life_status === 'alive' ? 'حيّ' : 'متوفّى'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="card">
            <h2 className="text-lg font-bold text-gov-dark">طلب تغيير جديد</h2>
            <form className="mt-3 space-y-3" onSubmit={submit}>
              <label className="block text-sm">
                <span className="text-slate-700">نوع الطلب</span>
                <select
                  className="mt-1 block w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm"
                  value={requestType}
                  onChange={(e) => setRequestType(e.target.value as ChangeRequestType)}
                >
                  {(Object.keys(REQUEST_TYPE_LABELS) as ChangeRequestType[]).map((k) => (
                    <option key={k} value={k}>
                      {REQUEST_TYPE_LABELS[k]}
                    </option>
                  ))}
                </select>
              </label>

              {needsPerson && (
                <>
                  <label className="block text-sm">
                    <span className="text-slate-700">الاسم الكامل</span>
                    <input
                      type="text"
                      className="mt-1 block w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      required={requestType === 'birth' || requestType === 'add_member'}
                    />
                  </label>
                  <label className="block text-sm">
                    <span className="text-slate-700">تاريخ الميلاد</span>
                    <input
                      type="date"
                      className="mt-1 block w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm"
                      value={birthDate}
                      onChange={(e) => setBirthDate(e.target.value)}
                    />
                  </label>
                  {(requestType === 'birth' || requestType === 'add_member') && (
                    <>
                      <label className="block text-sm">
                        <span className="text-slate-700">الجنس</span>
                        <select
                          className="mt-1 block w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm"
                          value={gender}
                          onChange={(e) => setGender(e.target.value as Gender)}
                        >
                          <option value="male">ذكر</option>
                          <option value="female">أنثى</option>
                        </select>
                      </label>
                      <label className="block text-sm">
                        <span className="text-slate-700">صلة القرابة</span>
                        <select
                          className="mt-1 block w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm"
                          value={relation}
                          onChange={(e) => setRelation(e.target.value as RelationToHead)}
                        >
                          {(Object.keys(RELATION_LABELS) as RelationToHead[]).map((k) => (
                            <option key={k} value={k}>
                              {RELATION_LABELS[k]}
                            </option>
                          ))}
                        </select>
                      </label>
                    </>
                  )}
                </>
              )}

              {needsTarget && (
                <label className="block text-sm">
                  <span className="text-slate-700">الفرد المعني</span>
                  <select
                    className="mt-1 block w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm"
                    value={targetPersonId}
                    onChange={(e) => setTargetPersonId(e.target.value)}
                    required
                  >
                    <option value="">— اختر —</option>
                    {household.members.map((m) => (
                      <option key={m.id} value={m.id}>
                        {m.full_name} ({RELATION_LABELS[m.relation_to_head]})
                      </option>
                    ))}
                  </select>
                </label>
              )}

              {requestType === 'address_change' && (
                <label className="block text-sm">
                  <span className="text-slate-700">العنوان الجديد</span>
                  <input
                    type="text"
                    className="mt-1 block w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm"
                    value={newAddress}
                    onChange={(e) => setNewAddress(e.target.value)}
                    required
                  />
                </label>
              )}

              <label className="block text-sm">
                <span className="text-slate-700">سبب الطلب (اختياري)</span>
                <textarea
                  className="mt-1 block w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm"
                  rows={2}
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                />
              </label>

              <button
                type="submit"
                className="btn-primary"
                disabled={submitting}
              >
                {submitting ? 'جارٍ الإرسال...' : 'إرسال الطلب'}
              </button>
            </form>
          </section>

          <section className="card">
            <h2 className="text-lg font-bold text-gov-dark">طلباتي السكانية</h2>
            {requests.length === 0 ? (
              <p className="mt-2 text-sm text-slate-500">لم تقدّم أي طلب بعد.</p>
            ) : (
              <ul className="mt-3 divide-y divide-slate-100">
                {requests.map((r) => (
                  <li key={r.id} className="flex items-center justify-between py-2 text-sm">
                    <div>
                      <p className="font-semibold text-slate-700">
                        طلب #{r.id} — {REQUEST_TYPE_LABELS[r.request_type]}
                      </p>
                      {r.mukhtar_comment && (
                        <p className="text-xs text-slate-500">
                          ملاحظة المختار: {r.mukhtar_comment}
                        </p>
                      )}
                    </div>
                    <span
                      className={`rounded-md px-2 py-1 text-xs ${
                        r.status === 'approved'
                          ? 'bg-emerald-50 text-emerald-700'
                          : r.status === 'rejected'
                          ? 'bg-rose-50 text-rose-700'
                          : 'bg-amber-50 text-amber-700'
                      }`}
                    >
                      {STATUS_LABELS[r.status] ?? r.status}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </div>
  );
}
