import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { ErrorBanner, LoadingBlock } from "../../components/ui/Feedback";
import { PageHeader } from "../../components/ui/PageHeader";
import {
  badgeClass,
  cardClass,
  secondaryButtonClass,
} from "../../components/ui/styles";
import { errorMessage } from "../../lib/format";
import { roleLabel } from "../../lib/roles";
import { studentsApi } from "../../services/api";
import type { Student } from "../../types/api";
import { useAuth } from "../auth/AuthContext";

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs font-medium uppercase tracking-wider text-slate-500">{label}</dt>
      <dd className="mt-1 text-sm font-medium text-slate-900">{value}</dd>
    </div>
  );
}

export function DashboardPage() {
  const { user } = useAuth();
  const student = useQuery<Student>({
    queryKey: ["students", "me"],
    queryFn: studentsApi.me,
    retry: false,
  });

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Student workspace"
        title={`Welcome, ${user?.display_name ?? "student"}`}
        description="Your institution profile and account state. Profile evidence and verified platform links arrive in Milestone 3."
        actions={
          <Link to="/student/profile" className={secondaryButtonClass}>
            Edit display details
          </Link>
        }
      />

      {student.isError ? <ErrorBanner message={errorMessage(student.error)} /> : null}
      {student.isPending ? <LoadingBlock label="Loading your student record…" /> : null}

      {student.isSuccess ? (
        <section className={`${cardClass} p-6`}>
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h2 className="text-base font-semibold text-slate-900">
                {student.data.display_name}
              </h2>
              <p className="mt-1 text-sm text-slate-500">{student.data.email}</p>
            </div>
            <span className={badgeClass}>{student.data.status}</span>
          </div>

          <dl className="mt-6 grid gap-5 border-t border-slate-100 pt-5 sm:grid-cols-2 lg:grid-cols-4">
            <Detail label="Register number" value={student.data.register_number} />
            <Detail label="Department" value={student.data.department_name} />
            <Detail label="Batch" value={student.data.batch_name} />
            <Detail
              label="Current year"
              value={student.data.current_year ? String(student.data.current_year) : "Not set"}
            />
          </dl>
        </section>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-2">
        <section className={`${cardClass} p-6`}>
          <h2 className="text-base font-semibold text-slate-900">Account</h2>
          <dl className="mt-4 space-y-4">
            <Detail label="Institution" value={user?.college_name ?? "—"} />
            <Detail label="Institution code" value={user?.college_code ?? "—"} />
            <Detail
              label="Roles"
              value={(user?.roles ?? []).map(roleLabel).join(", ") || "—"}
            />
          </dl>
        </section>

        <section className={`${cardClass} p-6`}>
          <h2 className="text-base font-semibold text-slate-900">What comes next</h2>
          <ul className="mt-4 space-y-3 text-sm text-slate-700">
            <li>Milestone 3 · Profile submission, evidence, mentor verification.</li>
            <li>Milestone 4 · Codeforces and GitHub connectors with async sync.</li>
            <li>Milestone 5 · Versioned scoring, coverage and rankings.</li>
          </ul>
          <p className="mt-4 rounded-lg bg-slate-50 p-3 text-xs text-slate-500">
            Missing evidence is reported as unknown, never as zero. Approved platform profiles
            become read-only.
          </p>
        </section>
      </div>
    </div>
  );
}
