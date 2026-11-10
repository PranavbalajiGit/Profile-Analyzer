import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { EmptyState, ErrorBanner, LoadingBlock } from "../../components/ui/Feedback";
import { PageHeader } from "../../components/ui/PageHeader";
import {
  badgeClass,
  cardClass,
  inputClass,
  labelClass,
  secondaryButtonClass,
  tableCellClass,
  tableClass,
  tableHeadClass,
} from "../../components/ui/styles";
import { errorMessage } from "../../lib/format";
import { isAdmin } from "../../lib/roles";
import { useDebouncedValue } from "../../lib/useDebouncedValue";
import { adminApi, studentsApi } from "../../services/api";
import type { StudentListParams } from "../../types/api";
import { useAuth } from "../auth/AuthContext";

const PAGE_SIZE = 20;
const STUDENT_STATUSES = ["ACTIVE", "GRADUATED", "SUSPENDED", "INACTIVE"];

export function StudentsPage() {
  const { user } = useAuth();
  const canFilterByCatalog = isAdmin(user);

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [batchId, setBatchId] = useState("");
  const [status, setStatus] = useState("");
  const debouncedSearch = useDebouncedValue(search.trim());

  const params: StudentListParams = {
    page,
    page_size: PAGE_SIZE,
    search: debouncedSearch || undefined,
    department_id: departmentId || undefined,
    batch_id: batchId || undefined,
    status: status || undefined,
  };

  const students = useQuery({
    queryKey: ["students", "list", params],
    queryFn: () => studentsApi.list(params),
  });

  const departments = useQuery({
    queryKey: ["admin", "departments"],
    queryFn: adminApi.listDepartments,
    enabled: canFilterByCatalog,
  });

  const batches = useQuery({
    queryKey: ["admin", "batches", "all"],
    queryFn: () => adminApi.listBatches(),
    enabled: canFilterByCatalog,
  });

  const visibleBatches = (batches.data ?? []).filter(
    (batch) => !departmentId || batch.department_id === departmentId,
  );

  const departmentCode = (id: string) =>
    departments.data?.find((department) => department.id === id)?.code ?? "—";

  const total = students.data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  function resetPage() {
    setPage(1);
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="People"
        title="Students"
        description="Students visible to your role. Mentors see only the batches assigned to them; college-wide roles see the whole institution."
      />

      <section className={`${cardClass} p-4`}>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <label className={labelClass} htmlFor="student-search">
              Search
            </label>
            <input
              id="student-search"
              className={inputClass}
              value={search}
              onChange={(event) => {
                setSearch(event.target.value);
                resetPage();
              }}
              placeholder="Name or register number"
            />
          </div>

          {canFilterByCatalog ? (
            <div>
              <label className={labelClass} htmlFor="student-department">
                Department
              </label>
              <select
                id="student-department"
                className={inputClass}
                value={departmentId}
                onChange={(event) => {
                  setDepartmentId(event.target.value);
                  setBatchId("");
                  resetPage();
                }}
              >
                <option value="">All departments</option>
                {(departments.data ?? []).map((department) => (
                  <option key={department.id} value={department.id}>
                    {department.code} · {department.name}
                  </option>
                ))}
              </select>
            </div>
          ) : null}

          {canFilterByCatalog ? (
            <div>
              <label className={labelClass} htmlFor="student-batch">
                Batch
              </label>
              <select
                id="student-batch"
                className={inputClass}
                value={batchId}
                onChange={(event) => {
                  setBatchId(event.target.value);
                  resetPage();
                }}
              >
                <option value="">All batches</option>
                {visibleBatches.map((batch) => (
                  <option key={batch.id} value={batch.id}>
                    {batch.name} · {departmentCode(batch.department_id)}
                  </option>
                ))}
              </select>
            </div>
          ) : null}

          <div>
            <label className={labelClass} htmlFor="student-status">
              Status
            </label>
            <select
              id="student-status"
              className={inputClass}
              value={status}
              onChange={(event) => {
                setStatus(event.target.value);
                resetPage();
              }}
            >
              <option value="">All statuses</option>
              {STUDENT_STATUSES.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </div>
        </div>
      </section>

      {students.isError ? <ErrorBanner message={errorMessage(students.error)} /> : null}
      {students.isPending ? <LoadingBlock label="Loading students…" /> : null}

      {students.isSuccess && students.data.items.length === 0 ? (
        <EmptyState>No students match the current filters.</EmptyState>
      ) : null}

      {students.isSuccess && students.data.items.length > 0 ? (
        <section className={`${cardClass} overflow-hidden`}>
          <div className="overflow-x-auto">
            <table className={tableClass}>
              <thead className={tableHeadClass}>
                <tr>
                  <th className="px-4 py-3">Register number</th>
                  <th className="px-4 py-3">Name</th>
                  <th className="px-4 py-3">Email</th>
                  <th className="px-4 py-3">Department</th>
                  <th className="px-4 py-3">Batch</th>
                  <th className="px-4 py-3">Year</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {students.data.items.map((student) => (
                  <tr key={student.id}>
                    <td className={`${tableCellClass} font-mono text-xs`}>
                      {student.register_number}
                    </td>
                    <td className={`${tableCellClass} font-medium text-slate-900`}>
                      {student.display_name}
                    </td>
                    <td className={tableCellClass}>{student.email}</td>
                    <td className={tableCellClass}>{student.department_name}</td>
                    <td className={tableCellClass}>{student.batch_name}</td>
                    <td className={tableCellClass}>{student.current_year ?? "—"}</td>
                    <td className={tableCellClass}>
                      <span className={badgeClass}>{student.status}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 px-4 py-3 text-sm text-slate-600">
            <span>
              Showing page {students.data.page} of {totalPages} · {total} student
              {total === 1 ? "" : "s"}
            </span>
            <div className="flex gap-2">
              <button
                type="button"
                className={secondaryButtonClass}
                onClick={() => setPage((current) => Math.max(1, current - 1))}
                disabled={page <= 1}
              >
                Previous
              </button>
              <button
                type="button"
                className={secondaryButtonClass}
                onClick={() => setPage((current) => Math.min(totalPages, current + 1))}
                disabled={page >= totalPages}
              >
                Next
              </button>
            </div>
          </div>
        </section>
      ) : null}
    </div>
  );
}
