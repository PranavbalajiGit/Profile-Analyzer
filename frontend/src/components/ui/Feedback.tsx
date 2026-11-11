import type { ReactNode } from "react";

export function LoadingBlock({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 text-sm text-slate-500 shadow-sm">
      {label}
    </div>
  );
}

export function ErrorBanner({ message }: { message: string }) {
  return (
    <div
      role="alert"
      className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
    >
      {message}
    </div>
  );
}

export function SuccessBanner({ children }: { children: ReactNode }) {
  return (
    <div
      role="status"
      className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800"
    >
      {children}
    </div>
  );
}

export function EmptyState({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-xl border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">
      {children}
    </div>
  );
}

export function ForbiddenPage() {
  return (
    <div className="mx-auto max-w-lg rounded-xl border border-amber-200 bg-amber-50 p-8 text-center">
      <p className="text-xs font-semibold uppercase tracking-wider text-amber-700">403</p>
      <h1 className="mt-2 text-xl font-semibold text-slate-900">Not available for your role</h1>
      <p className="mt-2 text-sm text-slate-600">
        Your account does not have permission to open this page. Contact your college
        administrator if you believe this is a mistake.
      </p>
    </div>
  );
}

export function FullPageLoader() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50">
      <div className="flex items-center gap-3 text-sm text-slate-500">
        <span className="size-4 animate-spin rounded-full border-2 border-slate-300 border-t-brand-600" />
        Loading your session…
      </div>
    </main>
  );
}
