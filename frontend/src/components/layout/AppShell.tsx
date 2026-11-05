import { NavLink, Outlet } from "react-router-dom";

const navigation = [{ to: "/student/dashboard", label: "Dashboard" }];

export function AppShell() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex w-full max-w-6xl items-center gap-6 px-4 py-3 sm:px-6">
          <NavLink to="/student/dashboard" className="flex items-center gap-3">
            <span className="flex size-9 items-center justify-center rounded-lg bg-brand-600 text-sm font-semibold text-white">
              PA
            </span>
            <span className="flex flex-col leading-tight">
              <span className="text-sm font-semibold text-slate-900">Profile Analyzer</span>
              <span className="text-xs text-slate-500">Technical performance platform</span>
            </span>
          </NavLink>

          <nav aria-label="Primary" className="ml-auto flex items-center gap-1">
            {navigation.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  [
                    "rounded-md px-3 py-2 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-brand-50 text-brand-700"
                      : "text-slate-600 hover:bg-slate-100 hover:text-slate-900",
                  ].join(" ")
                }
              >
                {item.label}
              </NavLink>
            ))}
            <span className="ml-3 hidden rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-medium text-amber-800 sm:inline">
              Milestone 1 · Foundation
            </span>
          </nav>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-6">
        <Outlet />
      </main>

      <footer className="border-t border-slate-200 bg-white">
        <div className="mx-auto flex w-full max-w-6xl flex-col gap-1 px-4 py-4 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <span>Profile Analyzer · V1</span>
          <span>Rankings are decision support, not automatic placement decisions.</span>
        </div>
      </footer>
    </div>
  );
}
