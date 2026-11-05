import { Link } from "react-router-dom";

export function LoginPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-12">
      <section className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
        <div className="mb-6 flex size-11 items-center justify-center rounded-lg bg-brand-600 text-sm font-semibold text-white">
          PA
        </div>

        <h1 className="text-xl font-semibold text-slate-900">Institutional sign-in</h1>
        <p className="mt-2 text-sm text-slate-600">
          Authentication is delivered in Milestone 2: OIDC with the college identity provider,
          plus an institution-provisioned password fallback.
        </p>

        <div className="mt-6 rounded-lg border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-600">
          No login form is shown yet. This page is a placeholder — it does not accept or store
          credentials.
        </div>

        <Link
          to="/student/dashboard"
          className="mt-6 inline-flex w-full items-center justify-center rounded-md bg-brand-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-brand-700"
        >
          View the foundation dashboard
        </Link>

        <p className="mt-4 text-center text-xs text-slate-500">
          Route guards are a UX convenience, never a security boundary.
        </p>
      </section>
    </main>
  );
}
