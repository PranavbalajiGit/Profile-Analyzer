import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";

import { EmptyState, ErrorBanner, LoadingBlock, SuccessBanner } from "../../components/ui/Feedback";
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

export function MentorsPage() {
  const queryClient = useQueryClient();
  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [employeeCode, setEmployeeCode] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [temporaryPassword, setTemporaryPassword] = useState("");
  const [mentorId, setMentorId] = useState("");
  const [batchId, setBatchId] = useState("");
  const [assigned, setAssigned] = useState<string | null>(null);

  const departments = useQuery({
    queryKey: ["admin", "departments"],
    queryFn: adminApi.listDepartments,
  });

  const batches = useQuery({
    queryKey: ["admin", "batches", "all"],
    queryFn: () => adminApi.listBatches(),
  });

  const mentors = useQuery({
    queryKey: ["admin", "mentors"],
    queryFn: adminApi.listMentors,
  });

  const createMentor = useMutation({
    mutationFn: adminApi.createMentor,
    onSuccess: async () => {
      setEmail("");
      setDisplayName("");
      setEmployeeCode("");
      setDepartmentId("");
      setTemporaryPassword("");
      await queryClient.invalidateQueries({ queryKey: ["admin", "mentors"] });
    },
  });

  const assignMentor = useMutation({
    mutationFn: ({ selectedMentor, selectedBatch }: { selectedMentor: string; selectedBatch: string }) =>
      adminApi.assignMentor(selectedMentor, selectedBatch),
    onSuccess: async (assignment) => {
      const mentor = mentors.data?.find((item) => item.id === assignment.mentor_id);
      const batch = batches.data?.find((item) => item.id === assignment.batch_id);
      setAssigned(
        `${mentor?.display_name ?? "Mentor"} assigned to ${batch?.name ?? "batch"}.`,
      );
      setMentorId("");
      setBatchId("");
      await queryClient.invalidateQueries({ queryKey: ["admin", "mentors"] });
    },
  });

  function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    createMentor.mutate({
      email: email.trim(),
      display_name: displayName.trim(),
      employee_code: employeeCode.trim(),
      department_id: departmentId || null,
      temporary_password: temporaryPassword,
    });
  }

  function handleAssign(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAssigned(null);
    assignMentor.mutate({ selectedMentor: mentorId, selectedBatch: batchId });
  }

  const departmentLabel = (id: string | null) => {
    if (!id) {
      return "—";
    }
    const department = departments.data?.find((item) => item.id === id);
    return department ? `${department.code} · ${department.name}` : "—";
  };

  const batchLabel = (id: string) => {
    const batch = batches.data?.find((item) => item.id === id);
    if (!batch) {
      return "—";
    }
    return `${batch.name} · ${departmentLabel(batch.department_id)}`;
  };

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="People"
        title="Mentors"
        description="Provision mentor accounts and assign them to department batches. Mentor approval authority is per platform and is introduced with profiles in Milestone 3."
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <section className={`${cardClass} p-6`}>
          <h2 className="text-base font-semibold text-slate-900">Provision a mentor</h2>
          <form className="mt-4 space-y-4" onSubmit={handleCreate}>
            <div>
              <label className={labelClass} htmlFor="mentor-email">
                Institutional email
              </label>
              <input
                id="mentor-email"
                type="email"
                className={inputClass}
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="mentor@college.example.edu"
                maxLength={320}
                required
              />
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className={labelClass} htmlFor="mentor-name">
                  Display name
                </label>
                <input
                  id="mentor-name"
                  className={inputClass}
                  value={displayName}
                  onChange={(event) => setDisplayName(event.target.value)}
                  maxLength={200}
                  required
                />
              </div>
              <div>
                <label className={labelClass} htmlFor="mentor-code">
                  Employee code
                </label>
                <input
                  id="mentor-code"
                  className={`${inputClass} font-mono`}
                  value={employeeCode}
                  onChange={(event) => setEmployeeCode(event.target.value)}
                  placeholder="CSE-M-002"
                  maxLength={64}
                  required
                />
              </div>
            </div>

            <div>
              <label className={labelClass} htmlFor="mentor-department">
                Department
              </label>
              <select
                id="mentor-department"
                className={inputClass}
                value={departmentId}
                onChange={(event) => setDepartmentId(event.target.value)}
              >
                <option value="">No department</option>
                {(departments.data ?? []).map((department) => (
                  <option key={department.id} value={department.id}>
                    {department.code} · {department.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className={labelClass} htmlFor="mentor-password">
                Temporary password
              </label>
              <input
                id="mentor-password"
                type="password"
                className={inputClass}
                value={temporaryPassword}
                onChange={(event) => setTemporaryPassword(event.target.value)}
                minLength={12}
                maxLength={256}
                required
              />
              <p className="mt-1 text-xs text-slate-500">
                At least 12 characters with uppercase, lowercase and a digit. Share it through a
                secure channel; the account starts active.
              </p>
            </div>

            {createMentor.isError ? (
              <ErrorBanner message={errorMessage(createMentor.error)} />
            ) : null}

            <button type="submit" className={primaryButtonClass} disabled={createMentor.isPending}>
              {createMentor.isPending ? "Provisioning…" : "Provision mentor"}
            </button>
          </form>
        </section>

        <section className={`${cardClass} p-6`}>
          <h2 className="text-base font-semibold text-slate-900">Assign a batch</h2>
          <form className="mt-4 space-y-4" onSubmit={handleAssign}>
            <div>
              <label className={labelClass} htmlFor="assign-mentor">
                Mentor
              </label>
              <select
                id="assign-mentor"
                className={inputClass}
                value={mentorId}
                onChange={(event) => setMentorId(event.target.value)}
                required
              >
                <option value="">Select a mentor</option>
                {(mentors.data ?? []).map((mentor) => (
                  <option key={mentor.id} value={mentor.id}>
                    {mentor.display_name} · {mentor.employee_code}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className={labelClass} htmlFor="assign-batch">
                Batch
              </label>
              <select
                id="assign-batch"
                className={inputClass}
                value={batchId}
                onChange={(event) => setBatchId(event.target.value)}
                required
              >
                <option value="">Select a batch</option>
                {(batches.data ?? []).map((batch) => (
                  <option key={batch.id} value={batch.id}>
                    {batchLabel(batch.id)}
                  </option>
                ))}
              </select>
            </div>

            {assignMentor.isError ? (
              <ErrorBanner message={errorMessage(assignMentor.error)} />
            ) : null}
            {assigned ? <SuccessBanner>{assigned}</SuccessBanner> : null}

            <button
              type="submit"
              className={primaryButtonClass}
              disabled={assignMentor.isPending || !mentorId || !batchId}
            >
              {assignMentor.isPending ? "Assigning…" : "Assign mentor"}
            </button>
          </form>
          <p className="mt-4 text-xs text-slate-500">
            Re-assigning an existing pair is idempotent. A mentor may hold several batch
            assignments.
          </p>
        </section>
      </div>

      {mentors.isError ? <ErrorBanner message={errorMessage(mentors.error)} /> : null}
      {mentors.isPending ? <LoadingBlock label="Loading mentors…" /> : null}

      {mentors.isSuccess && mentors.data.length === 0 ? (
        <EmptyState>No mentors provisioned yet.</EmptyState>
      ) : null}

      {mentors.isSuccess && mentors.data.length > 0 ? (
        <section className={`${cardClass} overflow-hidden`}>
          <div className="overflow-x-auto">
            <table className={tableClass}>
              <thead className={tableHeadClass}>
                <tr>
                  <th className="px-4 py-3">Name</th>
                  <th className="px-4 py-3">Email</th>
                  <th className="px-4 py-3">Employee code</th>
                  <th className="px-4 py-3">Department</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {mentors.data.map((mentor) => (
                  <tr key={mentor.id}>
                    <td className={`${tableCellClass} font-medium text-slate-900`}>
                      {mentor.display_name}
                    </td>
                    <td className={tableCellClass}>{mentor.email}</td>
                    <td className={`${tableCellClass} font-mono text-xs`}>
                      {mentor.employee_code}
                    </td>
                    <td className={tableCellClass}>{departmentLabel(mentor.department_id)}</td>
                    <td className={tableCellClass}>
                      <span className={badgeClass}>{mentor.status}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}
    </div>
  );
}
