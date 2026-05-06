'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useState } from 'react';

import { useAuth } from '../lib/auth-context';

const NAV_ITEMS = [
  { href: '/dashboard', label: 'الرئيسية' },
  { href: '/requests', label: 'طلباتي' },
  { href: '/services', label: 'كتالوج الخدمات' },
  { href: '/profile', label: 'الملف الشخصي' },
];

export default function Navbar() {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const [open, setOpen] = useState(false);

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  return (
    <header className="border-b border-slate-200 bg-white shadow-sm">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
        <div className="flex items-center gap-3">
          <Link href="/dashboard" className="flex items-center gap-2 text-gov">
            <span className="flex h-9 w-9 items-center justify-center rounded-md bg-gov text-white font-bold">
              س
            </span>
            <span className="text-lg font-bold text-gov-dark">سوريا الرقمية</span>
          </Link>
        </div>

        <nav className="hidden items-center gap-1 md:flex">
          {NAV_ITEMS.map((item) => {
            const isActive =
              pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`rounded-md px-3 py-2 text-sm font-medium transition ${
                  isActive
                    ? 'bg-gov-light text-gov-dark'
                    : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="hidden items-center gap-3 md:flex">
          {user && (
            <span className="text-sm text-slate-600">
              مرحباً، <span className="font-semibold text-slate-800">{user.full_name}</span>
            </span>
          )}
          <button type="button" onClick={handleLogout} className="btn-secondary">
            تسجيل الخروج
          </button>
        </div>

        <button
          type="button"
          aria-label="فتح القائمة"
          aria-expanded={open}
          className="md:hidden rounded-md border border-slate-200 p-2 text-slate-600"
          onClick={() => setOpen((value) => !value)}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
      </div>

      {open && (
        <div className="border-t border-slate-200 bg-white md:hidden">
          <nav className="space-y-1 px-4 py-3">
            {NAV_ITEMS.map((item) => {
              const isActive =
                pathname === item.href || pathname.startsWith(`${item.href}/`);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setOpen(false)}
                  className={`block rounded-md px-3 py-2 text-sm font-medium ${
                    isActive
                      ? 'bg-gov-light text-gov-dark'
                      : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
            <button
              type="button"
              onClick={() => {
                setOpen(false);
                handleLogout();
              }}
              className="block w-full rounded-md px-3 py-2 text-right text-sm font-medium text-rose-600 hover:bg-rose-50"
            >
              تسجيل الخروج
            </button>
          </nav>
        </div>
      )}
    </header>
  );
}
