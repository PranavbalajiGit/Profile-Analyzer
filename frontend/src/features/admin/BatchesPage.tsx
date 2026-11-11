import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";

import { EmptyState, ErrorBanner, LoadingBlock } from "../../components/ui/Feedback";
import { PageHeader } from "../../components/ui/PageHeader";
import {
  badgeClass,
  cardClass,
  inputClass,
  labelClass,
  primaryButtonClass,
  tableCellClass,
  tableClass,
  tableHeadClass,
} from "../../components/ui/styles";
import { errorMessage } from "../../lib/format";
import { adminApi } from "../../services/api";

const currentYear = new Date().getFullYear();

export function BatchesPage() {
  const queryClient = useQueryClient();
  const [departmentId, setDepartmentId] = useState("");
  const [filterDepartmentId, setFilterDepartmentId] = useState("");
  const [name, setName] = useState("");
  const [startYear, setStartYear] = useState(String(currentYear));
  const [endYear, setEndYear] = useState(String(currentYear + 4));

  const departments = useQuery({
    queryKey: ["admin", "departments"],
    queryFn: adminApi.listDepartments,
  });

  const batches = useQuery({
    queryKey: ["admin", "batches", filterDepartmentId || "all"],
    queryFn: () => adminApi.listBatches(filterDepartmentId || undefined),
  });

  const createBatch = useMutation({
    mutationFn: adminApi.createBatch,
    onSuccess: async () => {
      setName("");
      await queryClient.invalidateQueries({ queryKey: ["admin", "batches"] });
    },
  });

  function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    createBatch.mutate({
      department_id: departmentId,
      name: name.trim(),
      start_year: Number(startYear),
      end_year: Number(endYear),
    });
  }

  const departmentName = (id: string) =>
    departments.data?.find((department) => department.id === id);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Institution setup"
        title="Batches"
        description="A batch belongs to one department and records both its start and end year. Mentor-to-batch assignments are managed on the Mentors page."
      />

      <section className={`${cardClass} p-6`}>
        <h2 className="text-base font-semibold text-slate-900">Add a batch</h2>
        <form
          className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-[1fr_160px_120px_120px_auto] lg:items-end"
          onSubmit={handleCreate}
        >
          <div>
            <label className={labelClass} htmlFor="batch-department">
              Department
            </label>
            <select
              id="batch-department"
              className={inputClass}
              value={departmentId}
              onChange={(event) => setDepartmentId(event.target.value)}
              required
            >
              <option value="">Select a department</option>
              {(departments.data ?? []).map((department) => (
                <option key={department.id} value={department.id}>
                  {department.code} · {department.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className={labelClass} htmlFor="batch-name">
              Batch name
            </label>
            <input
              id="batch-name"
              className={inputClass}
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="2023-2027"
              maxLength={100}
              required
            />
          </div>

          <div>
            <label className={labelClass} htmlFor="batch-start">
              Start year
            </label>
            <input
              id="batch-start"
              type="number"
              className={inputClass}
              value={startYear}
              onChange={(event) => setStartYear(event.target.value)}
              min={1900}
              max={2200}
              required
            />
          </div>

          <div>
            <label className={labelClass} htmlFor="batch-end">
              End year
            </label>
            <input
              id="batch-end"
              type="number"
              className={inputClass}
              value={endYear}
              onChange={(event) => setEndYear(event.target.value)}
              min={1900}
              max={2300}
              required
            />
          </div>

          <button
            type="submit"
            className={primaryButtonClass}
            disabled={createBatch.isPending || !departmentId}
          >
            {createBatch.isPending ? "Adding…" : "Add batch"}
          </button>
        </form>
        {createBatch.isError ? (
          <div className="mt-4">
            <ErrorBanner message={errorMessage(createBatch.error)} />
          </div>
        ) : null}
      </section>

      <section className={`${cardClass} p-4`}>
        <label className={`${labelClass} max-w-xs`} htmlFor="batch-filter">
          Filter by department
        </label>
        <select
          id="batch-filter"
          className={`${inputClass} max-w-xs`}
          value={filterDepartmentId}
          onChange={(event) => setFilterDepartmentId(event.target.value)}
        >
          <option value="">All departments</option>
          {(departments.data ?? []).map((department) => (
            <option key={department.id} value={department.id}>
              {department.code} · {department.name}
            </option>
          ))}
        </select>
      </section>

      {batches.isError ? <ErrorBanner message={errorMessage(batches.error)} /> : null}
      {batches.isPending ? <LoadingBlock label="Loading batches…" /> : null}

      {batches.isSuccess && batches.data.length === 0 ? (
        <EmptyState>No batches found for this filter.</EmptyState>
      ) : null}

      {batches.isSuccess && batches.data.length > 0 ? (
        <section className={`${cardClass} overflow-hidden`}>
          <div className="overflow-x-auto">
            <table className={tableClass}>
              <thead className={tableHeadClass}>
                <tr>
                  <th className="px-4 py-3">Batch</th>
                  <th className="px-4 py-3">Department</th>
                  <th className="px-4 py-3">Start year</th>
                  <th className="px-4 py-3">End year</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {batches.data.map((batch) => {
                  const department = departmentName(batch.department_id);
                  return (
                    <tr key={batch.id}>
                      <td className={`${tableCellClass} font-medium text-slate-900`}>
                        {batch.name}
                      </td>
                      <td className={tableCellClass}>
                        {department ? `${department.code} · ${department.name}` : "—"}
                      </td>
                      <td className={tableCellClass}>{batch.start_year}</td>
                      <td className={tableCellClass}>{batch.end_year}</td>
                      <td className={tableCellClass}>
                        <span className={badgeClass}>{batch.status}</span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}
    </div>
  );
}
