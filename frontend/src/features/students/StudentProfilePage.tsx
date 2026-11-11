import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState, type FormEvent } from "react";

import { ErrorBanner, LoadingBlock, SuccessBanner } from "../../components/ui/Feedback";
import { PageHeader } from "../../components/ui/PageHeader";
import {
  cardClass,
  inputClass,
  labelClass,
  primaryButtonClass,
} from "../../components/ui/styles";
import { errorMessage } from "../../lib/format";
import { studentsApi } from "../../services/api";
import type { Student, StudentUpdate } from "../../types/api";

export function StudentProfilePage() {
  const queryClient = useQueryClient();
  const [displayName, setDisplayName] = useState("");
  const [currentYear, setCurrentYear] = useState("");
  const [saved, setSaved] = useState(false);

  const student = useQuery<Student>({
    queryKey: ["students", "me"],
    queryFn: studentsApi.me,
    retry: false,
  });

  useEffect(() => {
    if (student.data) {
      setDisplayName(student.data.display_name);
      setCurrentYear(student.data.current_year ? String(student.data.current_year) : "");
    }
  }, [student.data]);

  const mutation = useMutation({
    mutationFn: (payload: StudentUpdate) => studentsApi.updateMe(payload),
    onSuccess: (updated) => {
      queryClient.setQueryData(["students", "me"], updated);
      setSaved(true);
    },
  });

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaved(false);
    const payload: StudentUpdate = { display_name: displayName.trim() };
    if (currentYear !== "") {
      payload.current_year = Number(currentYear);
    }
    mutation.mutate(payload);
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Student profile"
        title="Display details"
        description="Update the display name and current year shown on your profile. Academic identifiers are managed by your college."
      />

      {student.isError ? <ErrorBanner message={errorMessage(student.error)} /> : null}
      {student.isPending ? <LoadingBlock label="Loading your student record…" /> : null}

      {student.isSuccess ? (
        <div className="grid gap-6 lg:grid-cols-3">
          <section className={`${cardClass} p-6 lg:col-span-2`}>
            <form className="space-y-4" onSubmit={handleSubmit}>
              <div>
                <label className={labelClass} htmlFor="display-name">
                  Display name
                </label>
                <input
                  id="display-name"
                  className={inputClass}
                  value={displayName}
                  onChange={(event) => setDisplayName(event.target.value)}
                  minLength={2}
                  maxLength={200}
                  required
                />
              </div>

              <div>
                <label className={labelClass} htmlFor="current-year">
                  Current year of study
                </label>
                <input
                  id="current-year"
                  type="number"
                  className={inputClass}
                  value={currentYear}
                  onChange={(event) => setCurrentYear(event.target.value)}
                  min={1}
                  max={8}
                  placeholder="Not set"
                />
              </div>

              {mutation.isError ? <ErrorBanner message={errorMessage(mutation.error)} /> : null}
              {saved ? <SuccessBanner>Profile updated.</SuccessBanner> : null}

              <button type="submit" className={primaryButtonClass} disabled={mutation.isPending}>
                {mutation.isPending ? "Saving…" : "Save changes"}
              </button>
            </form>
          </section>

          <section className={`${cardClass} p-6`}>
            <h2 className="text-sm font-semibold text-slate-900">College-managed</h2>
            <dl className="mt-4 space-y-4 text-sm">
              <div>
                <dt className="text-xs font-medium uppercase tracking-wider text-slate-500">
                  Register number
                </dt>
                <dd className="mt-1 font-medium text-slate-900">
                  {student.data.register_number}
                </dd>
              </div>
              <div>
                <dt className="text-xs font-medium uppercase tracking-wider text-slate-500">
                  Institutional email
                </dt>
                <dd className="mt-1 font-medium text-slate-900">{student.data.email}</dd>
              </div>
              <div>
                <dt className="text-xs font-medium uppercase tracking-wider text-slate-500">
                  Department
                </dt>
                <dd className="mt-1 font-medium text-slate-900">
                  {student.data.department_name}
                </dd>
              </div>
              <div>
                <dt className="text-xs font-medium uppercase tracking-wider text-slate-500">
                  Batch
                </dt>
                <dd className="mt-1 font-medium text-slate-900">{student.data.batch_name}</dd>
              </div>
            </dl>
            <p className="mt-4 text-xs text-slate-500">
              Contact your college administrator to correct these values.
            </p>
          </section>
        </div>
      ) : null}
    </div>
  );
}
