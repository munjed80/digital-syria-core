import './globals.css';
import type { Metadata } from 'next';
import { ReactNode } from 'react';

export const metadata: Metadata = {
  title: 'منصة سوريا الرقمية الأساسية',
  description: 'النسخة الأولية لإدارة الخدمات الحكومية الموحدة',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ar" dir="rtl">
      <body className="bg-slate-50 text-slate-900">{children}</body>
    </html>
  );
}
