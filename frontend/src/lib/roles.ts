import type { MeResponse, Role } from "../types/api";

export const ADMIN_ROLES: Role[] = ["COLLEGE_ADMIN", "SUPER_ADMIN"];
export const STUDENT_LIST_ROLES: Role[] = [
  "MENTOR",
  "PLACEMENT_COORDINATOR",
  "COLLEGE_ADMIN",
  "SUPER_ADMIN",
];

export function hasAnyRole(user: MeResponse | null, ...roles: Role[]): boolean {
  if (!user) {
    return false;
  }
  return roles.some((role) => user.roles.includes(role));
}

export function isAdmin(user: MeResponse | null): boolean {
  return hasAnyRole(user, ...ADMIN_ROLES);
}

export function isSuperAdmin(user: MeResponse | null): boolean {
  return hasAnyRole(user, "SUPER_ADMIN");
}

export function canListStudents(user: MeResponse | null): boolean {
  return hasAnyRole(user, ...STUDENT_LIST_ROLES);
}

export function homePathFor(user: MeResponse | null): string {
  if (!user) {
    return "/login";
  }
  if (hasAnyRole(user, "STUDENT")) {
    return "/student/dashboard";
  }
  if (isAdmin(user)) {
    return "/admin/departments";
  }
  return "/students";
}

const ROLE_LABELS: Record<Role, string> = {
  STUDENT: "Student",
  MENTOR: "Mentor",
  PLACEMENT_COORDINATOR: "Placement coordinator",
  COLLEGE_ADMIN: "College admin",
  SUPER_ADMIN: "Super admin",
};

export function roleLabel(role: Role): string {
  return ROLE_LABELS[role] ?? role;
}
