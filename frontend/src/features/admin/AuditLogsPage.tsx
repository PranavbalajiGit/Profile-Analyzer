import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { EmptyState, ErrorBanner, LoadingBlock } from "../../components/ui/Feedback";
import { PageHeader } from "../../components/ui/PageHeader";
import {
  cardClass,
  secondaryButtonClass,
  tableCellClass,
  tableClass,
  tableHeadClass,
} from "../../components/ui/styles";
import { errorMessage, formatDateTime, humanizeAction, shortId } from "../../lib/format";
import { adminApi } from "../../services/api";

const PAGE_SIZE = 20;

export function AuditLogsPage() {
  const [page, setPage] = useState(1);

  const logs = useQuery({
    queryKey: ["admin", "audit-logs", page],
    queryFn: () => adminApi.listAuditLogs({ page, page_size: PAGE_SIZE }),
  });

  const total = logs.data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Governance"
        title="Audit log"
        description="Append-only history of sensitive actions in your college. The application role can insert and read these rows but never update or delete them."
      />

      {logs.isError ? <ErrorBanner message={errorMessage(logs.error)} /> : null}
      {logs.isPending ? <LoadingBlock label="Loading audit events…" /> : null}

      {logs.isSuccess && logs.data.items.length === 0 ? (
        <EmptyState>No audit events recorded yet.</EmptyState>
      ) : null}

      {logs.isSuccess && logs.data.items.length > 0 ? (
        <section className={`${cardClass} overflow-hidden`}>
          <div className="overflow-x-auto">
            <table className={tableClass}>
              <thead className={tableHeadClass}>
                <tr>
                  <th className="px-4 py-3">Occurred</th>
                  <th className="px-4 py-3">Action</th>
                  <th className="px-4 py-3">Entity</th>
                  <th className="px-4 py-3">Entity ID</th>
                  <th className="px-4 py-3">Actor</th>
                  <th className="px-4 py-3">Request</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {logs.data.items.map((entry) => (
                  <tr key={entry.id}>
                    <td className={tableCellClass}>{formatDateTime(entry.occurred_at)}</td>
                    <td className={`${tableCellClass} font-medium text-slate-900`}>
                      {humanizeAction(entry.action)}
                    </td>
                    <td className={tableCellClass}>{entry.entity_type}</td>
                    <td className={`${tableCellClass} font-mono text-xs`}>
                      {shortId(entry.entity_id)}
                    </td>
                    <td className={`${tableCellClass} font-mono text-xs`}>
                      {shortId(entry.actor_user_id)}
                    </td>
                    <td className={`${tableCellClass} font-mono text-xs`}>
                      {shortId(entry.request_id)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 px-4 py-3 text-sm text-slate-600">
            <span>
              Showing page {logs.data.page} of {totalPages} · {total} event
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
