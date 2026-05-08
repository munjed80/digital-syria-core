'use client';

import { useEffect, useState } from 'react';

import { api, ApiError } from '../lib/api';
import type { PopulationStatistics } from '../lib/types';

const REQUEST_STATUS_LABELS: Record<string, string> = {
  submitted: 'مُرسل',
  mukhtar_review: 'بانتظار المختار',
  municipality_review: 'بانتظار البلدية',
  approved: 'مُعتمد',
  rejected: 'مرفوض',
};

interface Props {
  /** Page heading shown above the cards. */
  heading: string;
  /** Optional subheading text. */
  description?: string;
}

/**
 * Renders the population statistics for the currently authenticated user.
 *
 * The backend endpoint `/api/v1/population/statistics` already restricts the
 * data to the user's administrative scope, so the same component powers the
 * national admin, governor and municipality dashboards.
 */
export default function PopulationStatisticsView({ heading, description }: Props) {
  const [stats, setStats] = useState<PopulationStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api
      .populationStatistics()
      .then((data) => {
        if (!cancelled) setStats(data);
      })
      .catch((err) => {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 403) {
          setError('لا تملك صلاحية الوصول إلى إحصاءات السجل السكاني.');
        } else if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError('تعذّر تحميل الإحصاءات.');
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
        <h1 className="text-2xl font-bold text-gov-dark">{heading}</h1>
        {description && (
          <p className="mt-1 text-sm text-slate-600">{description}</p>
        )}
        {stats && (
          <p className="mt-1 text-xs text-slate-500">
            النطاق: <span className="font-semibold">{stats.scope_label}</span>
          </p>
        )}
      </header>

      {error && (
        <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
          {error}
        </div>
      )}

      {loading && !stats && (
        <p className="text-sm text-slate-500">جاري تحميل الإحصاءات...</p>
      )}

      {stats && (
        <>
          <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="إجمالي السكان" value={stats.total_population} />
            <StatCard label="إجمالي الأسر" value={stats.total_households} />
            <StatCard label="ولادات (آخر سنة)" value={stats.births_last_year} />
            <StatCard label="وفيات (آخر سنة)" value={stats.deaths_last_year} />
            <StatCard label="أسر موثّقة" value={stats.verified_households} tone="success" />
            <StatCard label="أسر بانتظار التحقق" value={stats.pending_households} tone="warning" />
            <StatCard label="ذكور" value={stats.gender.male} />
            <StatCard label="إناث" value={stats.gender.female} />
          </section>

          <section className="card">
            <h2 className="text-lg font-bold text-gov-dark">التوزيع العمري</h2>
            <div className="mt-3 grid gap-2 sm:grid-cols-3 lg:grid-cols-6">
              {stats.age_groups.map((g) => (
                <div
                  key={g.label}
                  className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-center"
                >
                  <p className="text-xs text-slate-500">{g.label}</p>
                  <p className="text-lg font-bold text-gov-dark">{g.count}</p>
                </div>
              ))}
              {stats.age_groups.length === 0 && (
                <p className="text-sm text-slate-500">لا توجد بيانات.</p>
              )}
            </div>
          </section>

          <section className="card">
            <h2 className="text-lg font-bold text-gov-dark">طلبات التغيير حسب الحالة</h2>
            {stats.requests_by_status.length === 0 ? (
              <p className="mt-2 text-sm text-slate-500">لا توجد طلبات حالياً.</p>
            ) : (
              <ul className="mt-3 space-y-1 text-sm">
                {stats.requests_by_status.map((s) => (
                  <li key={s.label} className="flex justify-between border-b border-slate-100 py-1">
                    <span>{REQUEST_STATUS_LABELS[s.label] ?? s.label}</span>
                    <span className="font-semibold text-gov-dark">{s.count}</span>
                  </li>
                ))}
              </ul>
            )}
          </section>

          {stats.administrative_breakdown.length > 0 && (
            <section className="card">
              <h2 className="text-lg font-bold text-gov-dark">التوزّع الإداري</h2>
              <div className="mt-3 overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-200 text-slate-500">
                      <th className="px-3 py-2 text-right">الوحدة</th>
                      <th className="px-3 py-2 text-right">عدد الأسر</th>
                      <th className="px-3 py-2 text-right">عدد السكان</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stats.administrative_breakdown.map((row) => (
                      <tr key={row.id} className="border-b border-slate-100">
                        <td className="px-3 py-2 font-medium text-slate-700">{row.name_ar}</td>
                        <td className="px-3 py-2">{row.households}</td>
                        <td className="px-3 py-2">{row.population}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}

function StatCard({
  label,
  value,
  tone = 'default',
}: {
  label: string;
  value: number;
  tone?: 'default' | 'success' | 'warning';
}) {
  const colour =
    tone === 'success'
      ? 'text-emerald-700'
      : tone === 'warning'
      ? 'text-amber-700'
      : 'text-gov-dark';
  return (
    <div className="card">
      <p className="text-sm text-slate-500">{label}</p>
      <p className={`mt-2 text-3xl font-bold ${colour}`}>{value}</p>
    </div>
  );
}
