// Los roles en el auth-service real NO son un enum: son un role_id (UUID)
// fijo, sin tabla de catálogo propia (ese catálogo vive en un futuro Role
// Management Service que todavía no existe). Estos tres UUID están
// hardcodeados en services/auth-service/app/core/config.py del backend —
// deben coincidir exactamente aquí para poder traducir role_id -> Role.
import type { Role } from "../types";

export const MENTEE_ROLE_ID = "123e4567-e89b-12d3-a456-426614174000";
export const MENTOR_ROLE_ID = "223e4567-e89b-12d3-a456-426614174000";
export const ADMIN_ROLE_ID = "323e4567-e89b-12d3-a456-426614174000";

const ROLE_ID_TO_ROLE: Record<string, Role> = {
  [MENTEE_ROLE_ID]: "mentee",
  [MENTOR_ROLE_ID]: "mentor",
  [ADMIN_ROLE_ID]: "admin",
};

const ROLE_TO_ROLE_ID: Record<Role, string> = {
  mentee: MENTEE_ROLE_ID,
  mentor: MENTOR_ROLE_ID,
  admin: ADMIN_ROLE_ID,
};

export function roleIdToRole(roleId: string): Role {
  return ROLE_ID_TO_ROLE[roleId] ?? "mentee";
}

export function roleToRoleId(role: Role): string {
  return ROLE_TO_ROLE_ID[role];
}
