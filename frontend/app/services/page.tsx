'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';

import { api, ApiError } from '../../lib/api';
import {
  groupServicesByCategory,
  SERVICE_CATEGORIES,
} from '../../lib/services-meta';
import type { ServiceItem } from '../../lib/types';

export default function ServicesPage() {
  const [services, setServices] = useState<ServiceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api
      .listServices()
      .then((data) => {
        if (!cancelled) setServices(data);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof ApiError ? err.message : 'تعذّر تحميل الخدمات.');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const grouped = useMemo(() => {
    const term = search.trim().toLowerCase();
    const filtered = term
      ? services.filter(
          (s) =>
            s.title_ar.toLowerCase().includes(term) ||
            s.description_ar.toLowerCase().includes(term) ||
            s.code.toLowerCase().includes(term),
        )
      : services;
    return groupServicesByCategory(filtered);
  }, [services, search]);

  return (
    <div className="space-y-8">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gov-dark">كتالوج الخدمات الحكومية</h1>
          <p className="mt-1 text-sm text-slate-600">
            استعرض الخدمات المتاحة مصنفةً حسب القطاع وقدّم طلبك إلكترونياً.
          </p>
        </div>
        <div className="w-full sm:w-72">
          <label htmlFor="search" className="sr-only">
            بحث عن خدمة
          </label>
          <input
            id="search"
            type="search"
            placeholder="ابحث عن خدمة..."
            className="form-input"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </header>

      {loading && <p className="text-sm text-slate-500">جاري تحميل الخدمات...</p>}
      {error && (
        <div className="rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {error}
        </div>
      )}

      {!loading && !error && services.length === 0 && (
        <div className="card text-center text-sm text-slate-600">
          لا توجد خدمات متاحة حالياً.
        </div>
      )}

      {!loading && !error && services.length > 0 && (
        <div className="space-y-10">
          {SERVICE_CATEGORIES.map((category) => {
            const items = grouped[category.key] || [];
            if (items.length === 0) return null;
            return (
              <section key={category.key}>
                <div className="mb-3 flex items-baseline justify-between">
                  <h2 className="text-lg font-bold text-gov-dark">
                    {category.title_ar}
                  </h2>
                  <span className="text-xs text-slate-500">
                    {items.length} خدمة
                  </span>
                </div>
                <p className="mb-4 text-sm text-slate-600">{category.description_ar}</p>
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {items.map((service) => (
                    <article
                      key={service.id}
                      className="card flex h-full flex-col justify-between"
                    >
                      <div>
                        <p className="text-xs font-mono text-slate-400">{service.code}</p>
                        <h3 className="mt-1 text-base font-bold text-slate-800">
                          {service.title_ar}
                        </h3>
                        <p className="mt-2 text-sm leading-6 text-slate-600">
                          {service.description_ar}
                        </p>
                      </div>
                      <div className="mt-4">
                        <Link
                          href={`/services/${service.id}/apply`}
                          className="btn-primary w-full"
                        >
                          تقديم طلب
                        </Link>
                      </div>
                    </article>
                  ))}
                </div>
              </section>
            );
          })}
        </div>
      )}
    </div>
  );
}
