'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { FormEvent, useState } from 'react';

import { ApiError } from '../../lib/api';
import { useAuth } from '../../lib/auth-context';

export default function RegisterPage() {
  const router = useRouter();
  const { register } = useAuth();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const validate = (): string | null => {
    if (!fullName.trim() || fullName.trim().length < 3) {
      return 'يرجى إدخال الاسم الكامل (٣ أحرف على الأقل).';
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email.trim())) {
      return 'البريد الإلكتروني غير صالح.';
    }
    if (password.length < 8) {
      return 'كلمة المرور يجب أن تكون ٨ أحرف على الأقل.';
    }
    if (password !== confirmPassword) {
      return 'كلمتا المرور غير متطابقتين.';
    }
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

    setSubmitting(true);
    try {
      await register(fullName.trim(), email.trim(), password);
      router.replace('/dashboard');
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('تعذّر إنشاء الحساب. حاول مرة أخرى.');
      }
    } finally {
      setSubmitting(false);
    }
  };

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

        <div className="card">
          <h1 className="mb-1 text-2xl font-bold text-gov-dark">إنشاء حساب جديد</h1>
          <p className="mb-6 text-sm text-slate-600">
            أنشئ حسابك للبدء بتقديم الطلبات الإلكترونية.
          </p>

          {error && (
            <div className="mb-4 rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            <div>
              <label htmlFor="full_name" className="form-label">
                الاسم الكامل
              </label>
              <input
                id="full_name"
                name="full_name"
                type="text"
                autoComplete="name"
                required
                minLength={3}
                className="form-input"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
              />
            </div>

            <div>
              <label htmlFor="email" className="form-label">
                البريد الإلكتروني
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
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
                autoComplete="new-password"
                required
                minLength={8}
                className="form-input"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                dir="ltr"
              />
              <p className="mt-1 text-xs text-slate-500">٨ أحرف على الأقل.</p>
            </div>

            <div>
              <label htmlFor="confirm_password" className="form-label">
                تأكيد كلمة المرور
              </label>
              <input
                id="confirm_password"
                name="confirm_password"
                type="password"
                autoComplete="new-password"
                required
                minLength={8}
                className="form-input"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                dir="ltr"
              />
            </div>

            <button type="submit" disabled={submitting} className="btn-primary w-full">
              {submitting ? 'جاري إنشاء الحساب...' : 'إنشاء حساب'}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-slate-600">
            لديك حساب بالفعل؟{' '}
            <Link href="/login" className="font-semibold text-gov hover:underline">
              تسجيل الدخول
            </Link>
          </p>
        </div>
      </div>
    </main>
  );
}
