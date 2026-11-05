import { useQuery } from "@tanstack/react-query";

import { fetchHealth } from "../../services/api";

const stack = [
  "Python + FastAPI",
  "PostgreSQL + SQLAlchemy + Alembic",
  "Redis + Celery",
  "React + TypeScript + Tailwind",
];

const nextMilestones = [
  { id: "M2", label: "Identity, tenants, departments, batches, RBAC" },
  { id: "M3", label: "Profile submission and mentor verification" },
  { id: "M4", label: "Codeforces and GitHub connectors, async sync" },
  { id: "M5", label: "Versioned scoring, coverage, rankings" },
];

export function DashboardPage() {
  const health = useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
    refetchInterval: 30_000,
  });

  const backendState = health.isPending
    ? "Checking…"
    : health.isSuccess
      ? `Connected · v${health.data.version}`
      : "Not reachable";

  return (
    <div className="space-y-8">
      <section>
        <p className="text-xs font-semibold uppercase tracking-wider text-brand-700">
          Milestone 1
        </p>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
          Foundation is in place
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-slate-600">
          This shell proves the frontend, API, database migrations, and worker wiring. Business
          modules start at Milestone 2, after identity and tenant boundaries.
        </p>
      </section>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-sm font-medium text-slate-500">Backend API</h2>
          <p className="mt-2 text-lg font-semibold text-slate-900">{backendState}</p>
          <p className="mt-1 text-xs text-slate-500">
            {health.isSuccess ? (
              <>
                {health.data.name} · {health.data.environment}
              </>
            ) : (
              "Start the API with docker compose up, or uvicorn in backend/."
            )}
          </p>
        </article>

        <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-sm font-medium text-slate-500">API surface</h2>
          <p className="mt-2 text-lg font-semibold text-slate-900">/api/v1</p>
          <p className="mt-1 text-xs text-slate-500">
            Health, readiness, request IDs, structured logs, error envelope.
          </p>
        </article>

        <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-sm font-medium text-slate-500">Evidence policy</h2>
          <p className="mt-2 text-lg font-semibold text-slate-900">Missing ≠ zero</p>
          <p className="mt-1 text-xs text-slate-500">
            Coverage is reported separately from performance in Milestone 5.
          </p>
        </article>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-base font-semibold text-slate-900">Stack</h2>
          <ul className="mt-4 space-y-2">
            {stack.map((item) => (
              <li key={item} className="flex items-start gap-3 text-sm text-slate-700">
                <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-brand-600" />
                {item}
              </li>
            ))}
          </ul>
        </section>

        <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-base font-semibold text-slate-900">Next milestones</h2>
          <ul className="mt-4 divide-y divide-slate-100">
            {nextMilestones.map((milestone) => (
              <li key={milestone.id} className="flex gap-3 py-2.5 text-sm">
                <span className="w-8 shrink-0 font-mono text-xs font-semibold text-brand-700">
                  {milestone.id}
                </span>
                <span className="text-slate-700">{milestone.label}</span>
              </li>
            ))}
          </ul>
        </section>
      </div>

      <section className="rounded-xl border border-slate-200 bg-slate-900 p-6 text-slate-100 shadow-sm">
        <h2 className="text-base font-semibold">Security boundaries from day one</h2>
        <ul className="mt-3 grid gap-2 text-sm text-slate-300 sm:grid-cols-2">
          <li>Tenant comes from the authenticated context, never the client.</li>
          <li>PostgreSQL RLS will back up application-level scoping.</li>
          <li>Approved platform profiles become read-only for students.</li>
          <li>No scraping, no undocumented endpoints, no fabricated metrics.</li>
        </ul>
      </section>
    </div>
  );
}
