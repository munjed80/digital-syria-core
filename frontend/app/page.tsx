import Link from 'next/link';

export default function HomePage() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-gov-light via-white to-white">
      <header className="border-b border-slate-200 bg-white/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-2 text-gov">
            <span className="flex h-9 w-9 items-center justify-center rounded-md bg-gov text-white font-bold">
              س
            </span>
            <span className="text-lg font-bold text-gov-dark">سوريا الرقمية</span>
          </div>
          <nav className="flex items-center gap-2">
            <Link href="/login" className="btn-secondary">
              تسجيل الدخول
            </Link>
            <Link href="/register" className="btn-primary">
              إنشاء حساب
            </Link>
          </nav>
        </div>
      </header>

      <section className="mx-auto max-w-5xl px-4 py-16 text-center sm:px-6 lg:py-24">
        <h1 className="text-4xl font-bold text-gov-dark sm:text-5xl">
          البوابة الموحدة للخدمات الحكومية الرقمية
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-lg leading-8 text-slate-700">
          منصة رسمية تتيح للمواطنين تقديم طلباتهم الإدارية ومتابعة حالتها في مكان واحد،
          بسهولة وأمان وشفافية.
        </p>
        <div className="mt-10 flex flex-wrap items-center justify-center gap-3">
          <Link href="/register" className="btn-primary px-6 py-3 text-base">
            ابدأ الآن
          </Link>
          <Link href="/login" className="btn-secondary px-6 py-3 text-base">
            لديك حساب؟ تسجيل الدخول
          </Link>
        </div>
      </section>

      <section className="mx-auto grid max-w-6xl gap-6 px-4 pb-20 sm:px-6 md:grid-cols-3">
        <div className="card">
          <h2 className="text-lg font-bold text-gov-dark">كتالوج الخدمات</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            استعرض الخدمات الحكومية المتاحة مصنفة حسب القطاع وقدِّم طلبك إلكترونياً.
          </p>
        </div>
        <div className="card">
          <h2 className="text-lg font-bold text-gov-dark">متابعة الطلبات</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            تابع حالة طلباتك لحظة بلحظة، من التقديم وحتى الإنجاز، مع سجل واضح للحالات.
          </p>
        </div>
        <div className="card">
          <h2 className="text-lg font-bold text-gov-dark">أمان وخصوصية</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            بنية تحتية آمنة، وصلاحيات دقيقة، وسجل تدقيق كامل لكل العمليات الحساسة.
          </p>
        </div>
      </section>

      <footer className="border-t border-slate-200 bg-white py-6 text-center text-sm text-slate-500">
        © منصة سوريا الرقمية — نسخة تجريبية
      </footer>
    </main>
  );
}
