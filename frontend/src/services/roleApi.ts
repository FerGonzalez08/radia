// Cliente HTTP de role-service (FastAPI, puerto 8002 en local — ver
// docker-compose.yml del repo de backend). Gestión de roles (HU008):
// listar usuarios con su rol y promover/revertir mentor <-> mentee.
//
// OJO: los endpoints antiguos `/auth/admin/users` y
// `PATCH /auth/admin/users/:id/role` (auth-service) ya NO EXISTEN — la
// gestión de roles se extrajo a este microservicio nuevo. UsersPage.tsx usa
// este módulo, no api.ts, para todo lo relacionado a roles.
import type { AdminUserRow } from "../types";
import { pickAvatarColor } from "./api";
import { roleIdToRole } from "./roles";
import { createApiClient } from "./httpClient";

const API_URL = (import.meta.env.VITE_ROLE_API_URL ?? "http://localhost:8002").replace(/\/$/, "");
const { request, authHeaders } = createApiClient(API_URL);

interface UserWithRoleOut {
  id: string;
  email: string;
  nombre: string;
  role_id: string;
  is_verified: boolean;
  is_active: boolean;
}

function mapUserRow(u: UserWithRoleOut): AdminUserRow {
  return {
    id: u.id,
    nombre: u.nombre,
    correo: u.email,
    rol: roleIdToRole(u.role_id),
    estado: !u.is_active ? "bloqueado" : !u.is_verified ? "pendiente" : "activo",
    avatarColor: pickAvatarColor(u.id),
  };
}

/** HU010 - Listado de usuarios con su rol actual (solo administrador). */
export async function listUsersWithRoles(accessToken: string): Promise<AdminUserRow[]> {
  const result = await request<UserWithRoleOut[]>("/roles/users", { headers: authHeaders(accessToken) });
  return result.map(mapUserRow);
}

/** HU008 - Promueve un mentee a mentora. Falla si ya es mentora o es admin. */
export async function promoteToMentor(accessToken: string, userId: string): Promise<AdminUserRow> {
  const result = await request<UserWithRoleOut>(`/roles/${userId}/promote`, {
    method: "POST",
    headers: authHeaders(accessToken),
  });
  return mapUserRow(result);
}

/** HU008 - Revierte una mentora a mentee. Falla si no es mentora actualmente. */
export async function revertToMentee(accessToken: string, userId: string): Promise<AdminUserRow> {
  const result = await request<UserWithRoleOut>(`/roles/${userId}/revert`, {
    method: "POST",
    headers: authHeaders(accessToken),
  });
  return mapUserRow(result);
}
