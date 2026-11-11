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

export function CollegesPage() {
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [shortCode, setShortCode] = useState("");
  const [domain, setDomain] = useState("");
  const [timezone, setTimezone] = useState("Asia/Kolkata");

  const colleges = useQuery({
    queryKey: ["admin", "colleges"],
    queryFn: adminApi.listColleges,
  });

  const createCollege = useMutation({
    mutationFn: adminApi.createCollege,
    onSuccess: async () => {
      setName("");
      setShortCode("");
      setDomain("");
      setTimezone("Asia/Kolkata");
      await queryClient.invalidateQueries({ queryKey: ["admin", "colleges"] });
    },
  });

  function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    createCollege.mutate({
      name: name.trim(),
      short_code: shortCode.trim().toUpperCase(),
      domain: domain.trim() || null,
      timezone: timezone.trim() || "Asia/Kolkata",
    });
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Platform administration"
        title="Colleges"
        description="Provision tenant institutions. This page is restricted to the platform super administrator; each college administrator only ever sees their own tenant."
      />

      <section className={`${cardClass} p-6`}>
        <h2 className="text-base font-semibold text-slate-900">Provision a college</h2>
        <form
          className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-[1fr_160px_1fr_180px_auto] lg:items-end"
          onSubmit={handleCreate}
        >
          <div>
            <label className={labelClass} htmlFor="college-name">
              Name
            </label>
            <input
              id="college-name"
              className={inputClass}
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="Northfield Institute of Technology"
              minLength={2}
              maxLength={200}
              required
            />
          </div>

          <div>
            <label className={labelClass} htmlFor="college-code">
              Short code
            </label>
            <input
              id="college-code"
              className={`${inputClass} font-mono uppercase`}
              value={shortCode}
              onChange={(event) => setShortCode(event.target.value)}
              placeholder="NFIT"
              minLength={2}
              maxLength={32}
              required
            />
          </div>

          <div>
            <label className={labelClass} htmlFor="college-domain">
              Email domain
            </label>
            <input
              id="college-domain"
              className={inputClass}
              value={domain}
              onChange={(event) => setDomain(event.target.value)}
              placeholder="northfield.example.edu"
              maxLength={255}
            />
          </div>

          <div>
            <label className={labelClass} htmlFor="college-timezone">
              Timezone
            </label>
            <input
              id="college-timezone"
              className={inputClass}
              value={timezone}
              onChange={(event) => setTimezone(event.target.value)}
              maxLength={64}
              required
            />
          </div>

          <button type="submit" className={primaryButtonClass} disabled={createCollege.isPending}>
            {createCollege.isPending ? "Provisioning…" : "Provision college"}
          </button>
        </form>
        {createCollege.isError ? (
          <div className="mt-4">
            <ErrorBanner message={errorMessage(createCollege.error)} />
          </div>
        ) : null}
      </section>

      {colleges.isError ? <ErrorBanner message={errorMessage(colleges.error)} /> : null}
      {colleges.isPending ? <LoadingBlock label="Loading colleges…" /> : null}

      {colleges.isSuccess && colleges.data.length === 0 ? (
        <EmptyState>No colleges provisioned yet.</EmptyState>
      ) : null}

      {colleges.isSuccess && colleges.data.length > 0 ? (
        <section className={`${cardClass} overflow-hidden`}>
          <div className="overflow-x-auto">
            <table className={tableClass}>
              <thead className={tableHeadClass}>
                <tr>
                  <th className="px-4 py-3">Short code</th>
                  <th className="px-4 py-3">Name</th>
                  <th className="px-4 py-3">Email domain</th>
                  <th className="px-4 py-3">Timezone</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {colleges.data.map((college) => (
                  <tr key={college.id}>
                    <td className={`${tableCellClass} font-mono text-xs font-semibold`}>
                      {college.short_code}
                    </td>
                    <td className={`${tableCellClass} font-medium text-slate-900`}>
                      {college.name}
                    </td>
                    <td className={tableCellClass}>{college.domain ?? "—"}</td>
                    <td className={tableCellClass}>{college.timezone}</td>
                    <td className={tableCellClass}>
                      <span className={badgeClass}>{college.status}</span>
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
