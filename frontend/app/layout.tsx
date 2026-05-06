import './globals.css';
import type { Metadata } from 'next';
import { ReactNode } from 'react';

import { AuthProvider } from '../lib/auth-context';

export const metadata: Metadata = {
  title: 'منصة سوريا الرقمية',
  description: 'البوابة الرسمية للخدمات الحكومية الموحدة',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ar" dir="rtl">
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
