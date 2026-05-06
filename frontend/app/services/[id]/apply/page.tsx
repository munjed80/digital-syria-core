'use client';

import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { FormEvent, useEffect, useState } from 'react';

import { api, ApiError } from '../../../../lib/api';
import type { ServiceItem, ServiceRequest } from '../../../../lib/types';

const TITLE_MAX = 255;
const DESCRIPTION_MIN = 10;
const DESCRIPTION_MAX = 2000;

export default function ApplyServicePage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const serviceId = Number(params?.id);

  const [service, setService] = useState<ServiceItem | null>(null);
  const [loadingService, setLoadingService] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [agree, setAgree] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [created, setCreated] = useState<ServiceRequest | null>(null);

  useEffect(() => {
    if (!Number.isFinite(serviceId)) {
      setLoadError('معرّف الخدمة غير صالح.');
      setLoadingService(false);
      return;
    }
    let cancelled = false;
    setLoadingService(true);
    api
      .listServices()
      .then((items) => {
        if (cancelled) return;
        const found = items.find((s) => s.id === serviceId) || null;
        if (!found) {
          setLoadError('الخدمة المطلوبة غير متاحة.');
        } else {
          setService(found);
          setTitle(`طلب: ${found.title_ar}`);
        }
      })
      .catch((err) => {
        if (cancelled) return;
        setLoadError(err instanceof ApiError ? err.message : 'تعذّر تحميل الخدمة.');
      })
      .finally(() => {
        if (!cancelled) setLoadingService(false);
      });
    return () => {
      cancelled = true;
    };
  }, [serviceId]);

  const validate = (): string | null => {
    if (!title.trim()) return 'يرجى إدخال عنوان الطلب.';
    if (title.trim().length > TITLE_MAX)
      return `عنوان الطلب يجب ألا يتجاوز ${TITLE_MAX} حرفاً.`;
    if (description.trim().length < DESCRIPTION_MIN)
      return `يرجى كتابة وصف لا يقل عن ${DESCRIPTION_MIN} أحرف.`;
    if (description.trim().length > DESCRIPTION_MAX)
      return `وصف الطلب يجب ألا يتجاوز ${DESCRIPTION_MAX} حرفاً.`;
    if (!agree) return 'يجب الإقرار بصحة المعلومات قبل التقديم.';
    return null;
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);

    const validationError = validate();
    if (validationError) {
      setError(validationError);
      return;
    }

    if (!service) return;
    setSubmitting(true);
    try {
      const result = await api.createRequest({
        service_id: service.id,
        title: title.trim(),
        description: description.trim(),
      });
      setCreated(result);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'تعذّر إرسال الطلب.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loadingService) {
    return <p className="text-sm text-slate-500">جاري تحميل بيانات الخدمة...</p>;
  }

  if (loadError || !service) {
    return (
      <div className="card">
        <p className="text-sm text-rose-600">{loadError || 'الخدمة غير متاحة.'}</p>
        <div className="mt-4">
          <Link href="/services" className="btn-secondary">
            العودة إلى الكتالوج
          </Link>
        </div>
      </div>
    );
  }

  if (created) {
    return (
      <div className="mx-auto max-w-2xl space-y-6">
        <div className="card border-emerald-200 bg-emerald-50">
          <h1 className="text-xl font-bold text-emerald-800">
            تم استلام طلبك بنجاح
          </h1>
          <p className="mt-2 text-sm text-emerald-900">
            سيتم مراجعة طلبك من قبل الجهة المختصة. يمكنك متابعة الحالة من خلال
            «طلباتي».
          </p>
          <div className="mt-4 rounded-md border border-emerald-200 bg-white p-4">
            <p className="text-sm text-slate-600">رقم تتبع الطلب</p>
            <p className="mt-1 text-2xl font-bold text-gov-dark">#{created.id}</p>
          </div>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link href={`/requests/${created.id}`} className="btn-primary">
            عرض تفاصيل الطلب
          </Link>
          <Link href="/requests" className="btn-secondary">
            الذهاب إلى طلباتي
          </Link>
          <button
            type="button"
            className="btn-secondary"
            onClick={() => router.push('/services')}
          >
            تصفّح خدمات أخرى
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <nav className="text-sm text-slate-500">
        <Link href="/services" className="hover:text-gov">
          كتالوج الخدمات
        </Link>{' '}
        / <span className="text-slate-700">{service.title_ar}</span>
      </nav>

      <header>
        <p className="text-xs font-mono text-slate-400">{service.code}</p>
        <h1 className="mt-1 text-2xl font-bold text-gov-dark">{service.title_ar}</h1>
        <p className="mt-2 text-sm leading-6 text-slate-600">{service.description_ar}</p>
      </header>

      <form onSubmit={handleSubmit} className="card space-y-5" noValidate>
        {error && (
          <div className="rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {error}
          </div>
        )}

        <div>
          <label htmlFor="title" className="form-label">
            عنوان الطلب
          </label>
          <input
            id="title"
            type="text"
            required
            maxLength={TITLE_MAX}
            className="form-input"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
        </div>

        <div>
          <label htmlFor="description" className="form-label">
            تفاصيل الطلب
          </label>
          <textarea
            id="description"
            required
            minLength={DESCRIPTION_MIN}
            maxLength={DESCRIPTION_MAX}
            rows={6}
            className="form-input"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="يرجى وصف طلبك بشكل واضح ومفصّل."
          />
          <p className="mt-1 text-xs text-slate-500">
            {description.length} / {DESCRIPTION_MAX} حرف
          </p>
        </div>

        <label className="flex items-start gap-2 text-sm text-slate-700">
          <input
            type="checkbox"
            checked={agree}
            onChange={(e) => setAgree(e.target.checked)}
            className="mt-1 h-4 w-4 rounded border-slate-300 text-gov focus:ring-gov"
          />
          <span>
            أُقرّ بأن جميع المعلومات المقدّمة صحيحة وأتحمل المسؤولية القانونية عن
            صحتها.
          </span>
        </label>

        <div className="flex flex-wrap items-center justify-end gap-3">
          <Link href="/services" className="btn-secondary">
            إلغاء
          </Link>
          <button type="submit" disabled={submitting} className="btn-primary">
            {submitting ? 'جاري الإرسال...' : 'إرسال الطلب'}
          </button>
        </div>
      </form>
    </div>
  );
}
