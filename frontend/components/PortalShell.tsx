'use client';

import { ReactNode } from 'react';

import Navbar from './Navbar';
import ProtectedRoute from './ProtectedRoute';

export default function PortalShell({ children }: { children: ReactNode }) {
  return (
    <ProtectedRoute>
      <div className="flex min-h-screen flex-col bg-slate-50">
        <Navbar />
        <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-8 sm:px-6 lg:px-8">
          {children}
        </main>
        <footer className="border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-500">
          © منصة سوريا الرقمية — نسخة تجريبية
        </footer>
      </div>
    </ProtectedRoute>
  );
}
