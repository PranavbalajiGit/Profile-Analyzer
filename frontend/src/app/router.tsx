import { createBrowserRouter } from "react-router-dom";

import { AppShell } from "../components/layout/AppShell";
import { ADMIN_ROLES, STUDENT_LIST_ROLES } from "../lib/roles";
import { AuditLogsPage } from "../features/admin/AuditLogsPage";
import { BatchesPage } from "../features/admin/BatchesPage";
import { CollegesPage } from "../features/admin/CollegesPage";
import { DepartmentsPage } from "../features/admin/DepartmentsPage";
import { ImportPage } from "../features/admin/ImportPage";
import { MentorsPage } from "../features/admin/MentorsPage";
import { LoginPage } from "../features/auth/LoginPage";
import { HomeRedirect } from "../features/auth/HomeRedirect";
import { RequireAuth, RequireRole } from "../features/auth/guards";
import { DashboardPage } from "../features/dashboard/DashboardPage";
import { NotFoundPage } from "../features/misc/NotFoundPage";
import { StudentProfilePage } from "../features/students/StudentProfilePage";
import { StudentsPage } from "../features/students/StudentsPage";

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  {
    path: "/",
    element: <RequireAuth />,
    children: [
      {
        element: <AppShell />,
        children: [
          { index: true, element: <HomeRedirect /> },
          {
            path: "student/dashboard",
            element: (
              <RequireRole roles={["STUDENT"]}>
                <DashboardPage />
              </RequireRole>
            ),
          },
          {
            path: "student/profile",
            element: (
              <RequireRole roles={["STUDENT"]}>
                <StudentProfilePage />
              </RequireRole>
            ),
          },
          {
            path: "students",
            element: (
              <RequireRole roles={STUDENT_LIST_ROLES}>
                <StudentsPage />
              </RequireRole>
            ),
          },
          {
            path: "admin/departments",
            element: (
              <RequireRole roles={ADMIN_ROLES}>
                <DepartmentsPage />
              </RequireRole>
            ),
          },
          {
            path: "admin/batches",
            element: (
              <RequireRole roles={ADMIN_ROLES}>
                <BatchesPage />
              </RequireRole>
            ),
          },
          {
            path: "admin/mentors",
            element: (
              <RequireRole roles={ADMIN_ROLES}>
                <MentorsPage />
              </RequireRole>
            ),
          },
          {
            path: "admin/import",
            element: (
              <RequireRole roles={ADMIN_ROLES}>
                <ImportPage />
              </RequireRole>
            ),
          },
          {
            path: "admin/audit",
            element: (
              <RequireRole roles={ADMIN_ROLES}>
                <AuditLogsPage />
              </RequireRole>
            ),
          },
          {
            path: "admin/colleges",
            element: (
              <RequireRole roles={["SUPER_ADMIN"]}>
                <CollegesPage />
              </RequireRole>
            ),
          },
        ],
      },
    ],
  },
  { path: "*", element: <NotFoundPage /> },
]);
