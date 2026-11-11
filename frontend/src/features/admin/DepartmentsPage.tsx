import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";

import { EmptyState, ErrorBanner, LoadingBlock } from "../../components/ui/Feedback";
import { PageHeader } from "../../components/ui/PageHeader";
import {
  badgeClass,
  cardClass,
  dangerButtonClass,
  inputClass,
  labelClass,
  primaryButtonClass,
  secondaryButtonClass,
  tableCellClass,
  tableClass,
  tableHeadClass,
} from "../../components/ui/styles";
import { errorMessage } from "../../lib/format";
import { adminApi } from "../../services/api";
import type { Department, DepartmentUpdate } from "../../types/api";

function DepartmentRow({
  department,
  onSave,
  saving,
}: {
  department: Department;
  onSave: (departmentId: string, payload: DepartmentUpdate) => void;
  saving: boolean;
}) {
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(department.name);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSave(department.id, { name: name.trim() });
    setEditing(false);
  }

  return (
    <tr>
      <td className={`${tableCellClass} font-mono text-xs`}>{department.code}</td>
      <td className={`${tableCellClass} w-full`}>
        {editing ? (
          <form className="flex items-center gap-2" onSubmit={submit}>
            <input
              className={inputClass}
              value={name}
              onChange={(event) => setName(event.target.value)}
              minLength={2}
              maxLength={200}
              required
              autoFocus
            />
            <button type="submit" className={secondaryButtonClass} disabled={saving}>
              Save
            </button>
            <button
              type="button"
              className={secondaryButtonClass}
              onClick={() => {
                setName(department.name);
                setEditing(false);
              }}
            >
              Cancel
            </button>
          </form>
        ) : (
          department.name
        )}
      </td>
      <td className={tableCellClass}>
        <span className={badgeClass}>{department.status}</span>
      </td>
      <td className={`${tableCellClass} text-right`}>
        <div className="flex justify-end gap-2">
          <button
            type="button"
            className={secondaryButtonClass}
            onClick={() => setEditing((current) => !current)}
          >
            Rename
          </button>
          <button
            type="button"
            className={department.status === "ACTIVE" ? dangerButtonClass : secondaryButtonClass}
            onClick={() =>
              onSave(department.id, {
                status: department.status === "ACTIVE" ? "INACTIVE" : "ACTIVE",
              })
            }
            disabled={saving}
          >
            {department.status === "ACTIVE" ? "Deactivate" : "Activate"}
          </button>
        </div>
      </td>
    </tr>
  );
}

export function DepartmentsPage() {
  const queryClient = useQueryClient();
  const [code, setCode] = useState("");
  const [name, setName] = useState("");

  const departments = useQuery({
    queryKey: ["admin", "departments"],
    queryFn: adminApi.listDepartments,
  });

  const createDepartment = useMutation({
    mutationFn: adminApi.createDepartment,
    onSuccess: async () => {
      setCode("");
      setName("");
      await queryClient.invalidateQueries({ queryKey: ["admin", "departments"] });
    },
  });

  const updateDepartment = useMutation({
    mutationFn: ({
      departmentId,
      payload,
    }: {
      departmentId: string;
      payload: DepartmentUpdate;
    }) => adminApi.updateDepartment(departmentId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["admin", "departments"] });
    },
  });

  function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    createDepartment.mutate({ code: code.trim().toUpperCase(), name: name.trim() });
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Institution setup"
        title="Departments"
        description="Departments belong to your college and scope batches, mentors and students. Codes are unique within the institution."
      />

      <section className={`${cardClass} p-6`}>
        <h2 className="text-base font-semibold text-slate-900">Add a department</h2>
        <form className="mt-4 grid gap-4 sm:grid-cols-[160px_1fr_auto] sm:items-end" onSubmit={handleCreate}>
          <div>
            <label className={labelClass} htmlFor="department-code">
              Code
            </label>
            <input
              id="department-code"
              className={`${inputClass} font-mono uppercase`}
              value={code}
              onChange={(event) => setCode(event.target.value)}
              placeholder="CSE"
              maxLength={32}
              required
            />
          </div>
          <div>
            <label className={labelClass} htmlFor="department-name">
              Name
            </label>
            <input
              id="department-name"
              className={inputClass}
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="Computer Science and Engineering"
              minLength={2}
              maxLength={200}
              required
            />
          </div>
          <button type="submit" className={primaryButtonClass} disabled={createDepartment.isPending}>
            {createDepartment.isPending ? "Adding…" : "Add department"}
          </button>
        </form>
        {createDepartment.isError ? (
          <div className="mt-4">
            <ErrorBanner message={errorMessage(createDepartment.error)} />
          </div>
        ) : null}
      </section>

      {updateDepartment.isError ? (
        <ErrorBanner message={errorMessage(updateDepartment.error)} />
      ) : null}
      {departments.isError ? <ErrorBanner message={errorMessage(departments.error)} /> : null}
      {departments.isPending ? <LoadingBlock label="Loading departments…" /> : null}

      {departments.isSuccess && departments.data.length === 0 ? (
        <EmptyState>No departments yet. Add the first one above.</EmptyState>
      ) : null}

      {departments.isSuccess && departments.data.length > 0 ? (
        <section className={`${cardClass} overflow-hidden`}>
          <div className="overflow-x-auto">
            <table className={tableClass}>
              <thead className={tableHeadClass}>
                <tr>
                  <th className="px-4 py-3">Code</th>
                  <th className="px-4 py-3">Name</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {departments.data.map((department) => (
                  <DepartmentRow
                    key={department.id}
                    department={department}
                    saving={updateDepartment.isPending}
                    onSave={(departmentId, payload) =>
                      updateDepartment.mutate({ departmentId, payload })
                    }
                  />
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}
    </div>
  );
}
