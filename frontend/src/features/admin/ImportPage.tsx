import { useMutation } from "@tanstack/react-query";
import { useRef, useState, type ChangeEvent, type FormEvent } from "react";

import { ErrorBanner, SuccessBanner } from "../../components/ui/Feedback";
import { PageHeader } from "../../components/ui/PageHeader";
import {
  cardClass,
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
import type { ImportResult } from "../../types/api";

const TEMPLATE = [
  "register_number,display_name,institutional_email,department_code,batch_name,admission_year,current_year,temporary_password",
  "CSE-001,Aarav Synthetic,aarav@college.example.edu,CSE,2023-2027,2023,3,ChangeMeNow1",
].join("\n");

export function ImportPage() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<ImportResult | null>(null);

  const importStudents = useMutation({
    mutationFn: adminApi.importStudents,
    onSuccess: (summary) => {
      setResult(summary);
      setFile(null);
      if (inputRef.current) {
        inputRef.current.value = "";
      }
    },
  });

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    setResult(null);
    setFile(event.target.files?.[0] ?? null);
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (file) {
      importStudents.mutate(file);
    }
  }

  function downloadTemplate() {
    const blob = new Blob([TEMPLATE], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "student-import-template.csv";
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Bulk onboarding"
        title="Import students"
        description="Upload a CSV or Excel file. Each valid row creates a user and a student record in your college. Rows are processed independently and every problem is reported back."
        actions={
          <button type="button" className={secondaryButtonClass} onClick={downloadTemplate}>
            Download CSV template
          </button>
        }
      />

      <section className={`${cardClass} p-6`}>
        <h2 className="text-base font-semibold text-slate-900">Upload a file</h2>
        <form className="mt-4 space-y-4" onSubmit={handleSubmit}>
          <div>
            <label className={labelClass} htmlFor="import-file">
              CSV or XLSX
            </label>
            <input
              id="import-file"
              ref={inputRef}
              type="file"
              accept=".csv,.xlsx"
              className={`${inputClass} file:mr-3 file:rounded file:border-0 file:bg-slate-100 file:px-3 file:py-1 file:text-sm file:font-medium`}
              onChange={handleFileChange}
              required
            />
          </div>

          <p className="text-xs text-slate-500">
            Required columns: register_number, display_name, institutional_email,
            department_code, batch_name. Optional: admission_year, current_year,
            temporary_password.
          </p>

          {importStudents.isError ? (
            <ErrorBanner message={errorMessage(importStudents.error)} />
          ) : null}

          <button
            type="submit"
            className={primaryButtonClass}
            disabled={!file || importStudents.isPending}
          >
            {importStudents.isPending ? "Importing…" : "Import students"}
          </button>
        </form>
      </section>

      {result ? (
        <section className={`${cardClass} p-6`}>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-base font-semibold text-slate-900">Import summary</h2>
            <SuccessBanner>Import finished. Review any skipped or failed rows.</SuccessBanner>
          </div>

          <dl className="mt-4 grid gap-4 sm:grid-cols-3">
            <div className="rounded-lg bg-emerald-50 p-4">
              <dt className="text-xs font-medium uppercase tracking-wider text-emerald-700">
                Created
              </dt>
              <dd className="mt-1 text-2xl font-semibold text-emerald-900">{result.created}</dd>
            </div>
            <div className="rounded-lg bg-amber-50 p-4">
              <dt className="text-xs font-medium uppercase tracking-wider text-amber-700">
                Skipped
              </dt>
              <dd className="mt-1 text-2xl font-semibold text-amber-900">{result.skipped}</dd>
            </div>
            <div className="rounded-lg bg-red-50 p-4">
              <dt className="text-xs font-medium uppercase tracking-wider text-red-700">
                Failed
              </dt>
              <dd className="mt-1 text-2xl font-semibold text-red-900">{result.failed}</dd>
            </div>
          </dl>

          {result.errors.length > 0 ? (
            <div className="mt-6 overflow-x-auto">
              <table className={tableClass}>
                <thead className={tableHeadClass}>
                  <tr>
                    <th className="px-4 py-3">Row</th>
                    <th className="px-4 py-3">Problem</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {result.errors.map((error, index) => (
                    <tr key={`${error.row}-${index}`}>
                      <td className={`${tableCellClass} font-mono text-xs`}>{error.row}</td>
                      <td className={`${tableCellClass} whitespace-normal`}>{error.message}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="mt-6 text-sm text-slate-600">No row-level errors were reported.</p>
          )}
        </section>
      ) : null}
    </div>
  );
}
