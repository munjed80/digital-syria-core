import type { RequestStatus, ServiceItem } from './types';

export interface ServiceCategory {
  key: string;
  title_ar: string;
  description_ar: string;
}

export const SERVICE_CATEGORIES: ServiceCategory[] = [
  {
    key: 'civil',
    title_ar: 'الأحوال المدنية',
    description_ar: 'الخدمات المتعلقة بالقيد المدني والوثائق الشخصية.',
  },
  {
    key: 'business',
    title_ar: 'الأعمال والتجارة',
    description_ar: 'تراخيص ومعاملات قطاع الأعمال.',
  },
  {
    key: 'municipal',
    title_ar: 'الخدمات البلدية',
    description_ar: 'الشكاوى والطلبات المتعلقة بالخدمات البلدية.',
  },
  {
    key: 'other',
    title_ar: 'خدمات أخرى',
    description_ar: 'خدمات حكومية متنوعة.',
  },
];

const PREFIX_TO_CATEGORY: Record<string, string> = {
  CIVIL: 'civil',
  BUSI: 'business',
  BUS: 'business',
  COMM: 'business',
  MUNI: 'municipal',
  MUN: 'municipal',
};

export function getServiceCategoryKey(service: ServiceItem): string {
  const prefix = (service.code || '').split('_')[0]?.toUpperCase() ?? '';
  return PREFIX_TO_CATEGORY[prefix] ?? 'other';
}

export function groupServicesByCategory(
  services: ServiceItem[],
): Record<string, ServiceItem[]> {
  const grouped: Record<string, ServiceItem[]> = {};
  for (const service of services) {
    const key = getServiceCategoryKey(service);
    if (!grouped[key]) grouped[key] = [];
    grouped[key].push(service);
  }
  return grouped;
}

export const STATUS_LABELS_AR: Record<RequestStatus, string> = {
  submitted: 'مقدَّم',
  under_review: 'قيد المراجعة',
  in_progress: 'قيد المعالجة',
  resolved: 'مكتمل',
  rejected: 'مرفوض',
};

export const STATUS_BADGE_CLASSES: Record<RequestStatus, string> = {
  submitted: 'bg-slate-100 text-slate-700',
  under_review: 'bg-amber-100 text-amber-800',
  in_progress: 'bg-blue-100 text-blue-800',
  resolved: 'bg-emerald-100 text-emerald-800',
  rejected: 'bg-rose-100 text-rose-800',
};

export function formatDateAr(value?: string | null): string {
  if (!value) return '—';
  try {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return '—';
    return new Intl.DateTimeFormat('ar', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date);
  } catch {
    return '—';
  }
}
