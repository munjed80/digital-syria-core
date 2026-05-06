'use client';

import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { FormEvent, Suspense, useState } from 'react';

import { ApiError } from '../../lib/api';
import { useAuth } from '../../lib/auth-context';

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);

    if (!email.trim() || !password) {
      setError('يرجى تعبئة جميع الحقول.');
      return;
    }

    setSubmitting(true);
    try {
      await login(email.trim(), password);
      const next = searchParams.get('next') || '/dashboard';
      router.replace(next);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('تعذّر تسجيل الدخول. حاول مرة أخرى.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="card">
      <h1 className="mb-1 text-2xl font-bold text-gov-dark">تسجيل الدخول</h1>
      <p className="mb-6 text-sm text-slate-600">
        ادخل بيانات حسابك للوصول إلى بوابة الخدمات.
      </p>

      {error && (
        <div className="mb-4 rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        <div>
          <label htmlFor="email" className="form-label">
            البريد الإلكتروني
          </label>
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="username"
            required
            className="form-input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            dir="ltr"
          />
        </div>

        <div>
          <label htmlFor="password" className="form-label">
            كلمة المرور
          </label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            required
            className="form-input"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            dir="ltr"
          />
        </div>

        <button type="submit" disabled={submitting} className="btn-primary w-full">
          {submitting ? 'جاري تسجيل الدخول...' : 'تسجيل الدخول'}
        </button>
      </form>

      <p className="mt-6 text-center text-sm text-slate-600">
        ليس لديك حساب؟{' '}
        <Link href="/register" className="font-semibold text-gov hover:underline">
          إنشاء حساب جديد
        </Link>
      </p>
    </div>
  );
}

export default function LoginPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-gov-light px-4 py-12">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <Link href="/" className="inline-flex items-center gap-2 text-gov-dark">
            <span className="flex h-10 w-10 items-center justify-center rounded-md bg-gov text-white font-bold">
              س
            </span>
            <span className="text-xl font-bold">سوريا الرقمية</span>
          </Link>
        </div>

        <Suspense
          fallback={
            <div className="card text-center text-sm text-slate-500">
              جاري التحميل...
            </div>
          }
        >
          <LoginForm />
        </Suspense>
      </div>
    </main>
  );
}
