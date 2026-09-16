// Cliente HTTP del auth-service real de RADIA (FastAPI, ver
// services/auth-service en el repo de backend que compartió Fernando).
// Reemplaza al antiguo mockApi.ts: mismos nombres de función donde tenía
// sentido conservarlos, pero ahora habla por fetch() con el backend real
// y traduce sus campos (snake_case, role_id como UUID) a los tipos que
// usa el resto del frontend.
import type { RegisterPayload, Sexo, User } from "../types";
import { roleIdToRole, roleToRoleId } from "./roles";

const API_BASE = (import.meta.env.VITE_API_URL ?? "http://localhost:8001").replace(/\/$/, "");

export class ApiError extends Error {
  field?: string;
  code?: string;
  meta?: Record<string, unknown>;
  constructor(message: string, opts?: { field?: string; code?: string; meta?: Record<string, unknown> }) {
    super(message);
    this.field = opts?.field;
    this.code = opts?.code;
    this.meta = opts?.meta;
  }
}

// El backend no expone color de avatar — se calcula igual que antes, a
// partir de un id estable, solo para que la UI tenga variedad visual.
const AVATAR_PALETTE = ["#D1155B", "#9A2177", "#682D90", "#B01B62", "#C81E63", "#4457D6"];
function pickAvatarColor(seed: string): string {
  let sum = 0;
  for (const c of seed) sum += c.charCodeAt(0);
  return AVATAR_PALETTE[sum % AVATAR_PALETTE.length];
}

interface BackendUserOut {
  id: string;
  email: string;
  nombre: string;
  telefono: string;
  sexo: string;
  fecha_nacimiento: string;
  role_id: string;
  is_verified: boolean;
  is_active: boolean;
  created_at: string;
}

function mapUser(u: BackendUserOut): User {
  return {
    id: u.id,
    nombre: u.nombre,
    correo: u.email,
    telefono: u.telefono,
    sexo: u.sexo as Sexo,
    fechaNacimiento: u.fecha_nacimiento,
    rol: roleIdToRole(u.role_id),
    estado: !u.is_active ? "bloqueado" : !u.is_verified ? "pendiente" : "activo",
    avatarColor: pickAvatarColor(u.id),
    creadoEn: u.created_at,
  };
}

// Traduce el `detail` que manda FastAPI (string en HTTPException, o una
// lista de errores de validación de Pydantic en un 422) a un ApiError con
// mensaje en español y, cuando aplica, un código que la UI puede revisar.
function toApiError(status: number, detail: unknown, fallbackField?: string): ApiError {
  const text = typeof detail === "string" ? detail : null;

  if (status === 0) {
    return new ApiError("No pudimos conectar con el servidor de RADIA. Verifica tu conexión e intenta de nuevo.", {
      code: "NETWORK_ERROR",
    });
  }

  if (status === 422) {
    // Errores de validación de Pydantic: [{ loc: ["body", "campo"], msg, ... }]
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0] as { loc?: unknown[]; msg?: string };
      const field = Array.isArray(first.loc) ? String(first.loc[first.loc.length - 1]) : undefined;
      return new ApiError("Verifica los datos ingresados.", { field: field ?? fallbackField, code: "VALIDATION_ERROR" });
    }
    return new ApiError("Verifica los datos ingresados.", { field: fallbackField, code: "VALIDATION_ERROR" });
  }

  if (status === 409) {
    return new ApiError(text ?? "Ese registro ya existe.", { field: fallbackField, code: "CONFLICT" });
  }

  if (status === 429) {
    return new ApiError(text ?? "Demasiados intentos. Intenta más tarde.", { code: "RATE_LIMITED" });
  }

  if (status === 401) {
    if (text === "Email not verified") {
      return new ApiError("Debes verificar tu cuenta antes de iniciar sesión.", { code: "NOT_VERIFIED" });
    }
    return new ApiError("Correo o contraseña incorrectos.", { code: "INVALID_CREDENTIALS" });
  }

  if (status === 403) {
    if (text === "Email not verified") {
      return new ApiError("Debes verificar tu cuenta antes de iniciar sesión.", { code: "NOT_VERIFIED" });
    }
    if (text === "Account is deactivated") {
      return new ApiError("Tu cuenta está desactivada. Contacta a una administradora.", { code: "ACCOUNT_DISABLED" });
    }
    return new ApiError("No tienes permisos para esta acción.", { code: "FORBIDDEN" });
  }

  if (status === 404) {
    return new ApiError(text ?? "No se encontró el recurso solicitado.", { code: "NOT_FOUND" });
  }

  if (status === 400) {
    return new ApiError(text ?? "Solicitud inválida.", { field: fallbackField, code: "BAD_REQUEST" });
  }

  return new ApiError(text ?? "Ocurrió un error inesperado. Intenta nuevamente.", { code: "UNKNOWN" });
}

async function request<T>(
  path: string,
  init: RequestInit & { fallbackField?: string } = {},
): Promise<T> {
  const { fallbackField, ...rest } = init;
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...rest,
      headers: {
        ...(rest.body ? { "Content-Type": "application/json" } : {}),
        ...(rest.headers ?? {}),
      },
    });
  } catch {
    throw toApiError(0, null, fallbackField);
  }

  if (res.status === 204) return undefined as T;

  const isJson = res.headers.get("content-type")?.includes("application/json");
  const body = isJson ? await res.json().catch(() => null) : null;

  if (!res.ok) {
    throw toApiError(res.status, body?.detail ?? null, fallbackField);
  }

  return body as T;
}

function authHeaders(accessToken: string): HeadersInit {
  return { Authorization: `Bearer ${accessToken}` };
}

// --- Registro (HU001) + Verificación por enlace de correo (HU002) --------

export async function register(payload: RegisterPayload): Promise<{ correo: string }> {
  await request<BackendUserOut>("/auth/register", {
    method: "POST",
    body: JSON.stringify({
      email: payload.correo.trim(),
      password: payload.password,
      nombre: payload.nombre.trim(),
      telefono: payload.telefono.trim(),
      sexo: payload.sexo,
      fecha_nacimiento: payload.fechaNacimiento,
    }),
    fallbackField: "correo",
  });
  return { correo: payload.correo.trim() };
}

export async function verifyEmail(token: string): Promise<void> {
  await request<void>("/auth/verify-email", {
    method: "POST",
    body: JSON.stringify({ token }),
  });
}

// --- Login (HU003) + tokens (HU004) ---------------------------------------

export interface TokenPair {
  accessToken: string;
  refreshToken: string;
}

export async function login(correo: string, password: string): Promise<TokenPair> {
  const result = await request<{ access_token: string; refresh_token: string }>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email: correo.trim(), password }),
  });
  return { accessToken: result.access_token, refreshToken: result.refresh_token };
}

export async function refreshTokenPair(refreshToken: string): Promise<TokenPair> {
  const result = await request<{ access_token: string; refresh_token: string }>("/auth/refresh", {
    method: "POST",
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  return { accessToken: result.access_token, refreshToken: result.refresh_token };
}

export async function logoutRemote(refreshToken: string): Promise<void> {
  try {
    await request<void>("/auth/logout", {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  } catch {
    // El cierre de sesión local no debe depender de que el backend
    // responda — si falla (red caída, token ya revocado), se ignora.
  }
}

export async function fetchMe(accessToken: string): Promise<User> {
  const result = await request<BackendUserOut>("/auth/me", { headers: authHeaders(accessToken) });
  return mapUser(result);
}

// --- Recuperación de contraseña (HU005) -----------------------------------

export async function requestPasswordReset(correo: string): Promise<{ message: string }> {
  await request<void>("/auth/password-reset/request", {
    method: "POST",
    body: JSON.stringify({ email: correo.trim() }),
  });
  // El backend responde 204 exista o no el correo (para no filtrar qué
  // cuentas existen) — el mensaje genérico se arma en el cliente.
  return { message: "Si el correo está registrado, te enviamos un enlace para restablecer tu contraseña." };
}

export async function resetPassword(token: string, password: string): Promise<void> {
  await request<void>("/auth/password-reset/confirm", {
    method: "POST",
    body: JSON.stringify({ token, new_password: password }),
  });
}

// --- Administración (HU008, HU010, HU011) ----------------------------------

export async function listAllUsers(accessToken: string): Promise<User[]> {
  const result = await request<BackendUserOut[]>("/auth/admin/users", { headers: authHeaders(accessToken) });
  return result.map(mapUser);
}

export async function updateUserRole(accessToken: string, userId: string, role: "mentee" | "mentor"): Promise<User> {
  const result = await request<BackendUserOut>(`/auth/admin/users/${userId}/role`, {
    method: "PATCH",
    headers: authHeaders(accessToken),
    body: JSON.stringify({ role_id: roleToRoleId(role) }),
  });
  return mapUser(result);
}
