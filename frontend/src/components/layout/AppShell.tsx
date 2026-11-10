import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { hasAnyRole, homePathFor, isAdmin, isSuperAdmin, roleLabel } from "../../lib/roles";
import type { Role } from "../../types/api";
import { useAuth } from "../../features/auth/AuthContext";

interface NavItem {
  to: string;
  label: string;
  roles?: Role[];
}

const navigation: NavItem[] = [
  { to: "/student/dashboard", label: "Dashboard", roles: ["STUDENT"] },
  { to: "/student/profile", label: "My profile", roles: ["STUDENT"] },
  {
    to: "/students",
    label: "Students",
    roles: ["MENTOR", "PLACEMENT_COORDINATOR", "COLLEGE_ADMIN", "SUPER_ADMIN"],
  },
  { to: "/admin/departments", label: "Departments", roles: ["COLLEGE_ADMIN", "SUPER_ADMIN"] },
  { to: "/admin/batches", label: "Batches", roles: ["COLLEGE_ADMIN", "SUPER_ADMIN"] },
  { to: "/admin/mentors", label: "Mentors", roles: ["COLLEGE_ADMIN", "SUPER_ADMIN"] },
  { to: "/admin/import", label: "Import", roles: ["COLLEGE_ADMIN", "SUPER_ADMIN"] },
  { to: "/admin/audit", label: "Audit log", roles: ["COLLEGE_ADMIN", "SUPER_ADMIN"] },
  { to: "/admin/colleges", label: "Colleges", roles: ["SUPER_ADMIN"] },
];

export function AppShell() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [signingOut, setSigningOut] = useState(false);

  if (!user) {
    return null;
  }

  const visibleNavigation = navigation.filter(
    (item) => !item.roles || hasAnyRole(user, ...item.roles),
  );
  const home = homePathFor(user);

  async function handleLogout() {
    setSigningOut(true);
    try {
      await logout();
      navigate("/login", { replace: true });
    } finally {
      setSigningOut(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex w-full max-w-6xl flex-wrap items-center gap-x-6 gap-y-3 px-4 py-3 sm:px-6">
          <NavLink to={home} className="flex items-center gap-3">
            <span className="flex size-9 items-center justify-center rounded-lg bg-brand-600 text-sm font-semibold text-white">
              PA
            </span>
            <span className="flex flex-col leading-tight">
              <span className="text-sm font-semibold text-slate-900">Profile Analyzer</span>
              <span className="text-xs text-slate-500">
                {user.college_name} · {user.college_code}
              </span>
            </span>
          </NavLink>

          <nav aria-label="Primary" className="flex flex-wrap items-center gap-1">
            {visibleNavigation.map((item) => (
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
          </nav>

          <div className="ml-auto flex items-center gap-3">
            <div className="hidden text-right leading-tight sm:block">
              <p className="text-sm font-medium text-slate-900">{user.display_name}</p>
              <p className="text-xs text-slate-500">
                {user.roles.map(roleLabel).join(", ")}
                {isSuperAdmin(user) ? " · platform" : isAdmin(user) ? " · college" : ""}
              </p>
            </div>
            <button
              type="button"
              onClick={handleLogout}
              disabled={signingOut}
              className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {signingOut ? "Signing out…" : "Sign out"}
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-6">
        <Outlet />
      </main>

      <footer className="border-t border-slate-200 bg-white">
        <div className="mx-auto flex w-full max-w-6xl flex-col gap-1 px-4 py-4 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <span>Profile Analyzer · Milestone 2 · Identity and access</span>
          <span>Rankings are decision support, not automatic placement decisions.</span>
        </div>
      </footer>
    </div>
  );
}
