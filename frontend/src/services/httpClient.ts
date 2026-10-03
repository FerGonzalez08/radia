// Cliente HTTP genérico, compartido por los cuatro microservicios de RADIA
// (auth, role, navigation, chat). Cada servicio expone su propio módulo
// (api.ts, roleApi.ts, navigationApi.ts, chatApi.ts) que llama a
// createApiClient(baseUrl) una vez y reexporta `request`/`authHeaders` — así
// la traducción de errores de FastAPI (Pydantic 422, HTTPException, etc.) a
// mensajes en español queda escrita en un solo lugar.
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

export type ErrorMapper = (status: number, detail: unknown, fallbackField?: string) => ApiError | undefined;

// Traduce el `detail` que manda FastAPI (string en HTTPException, o una
// lista de errores de validación de Pydantic en un 422) a un ApiError con
// mensaje en español y, cuando aplica, un código que la UI puede revisar.
function defaultMapError(status: number, detail: unknown, fallbackField?: string): ApiError {
  const text = typeof detail === "string" ? detail : null;

  if (status === 0) {
    return new ApiError("No pudimos conectar con el servidor de RADIA. Verifica tu conexión e intenta de nuevo.", {
      code: "NETWORK_ERROR",
    });
  }

  if (status === 422) {
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0] as { loc?: unknown[]; msg?: string };
      const field = Array.isArray(first.loc) ? String(first.loc[first.loc.length - 1]) : undefined;
      return new ApiError("Verifica los datos ingresados.", { field: field ?? fallbackField, code: "VALIDATION_ERROR" });
    }
    return new ApiError("Verifica los datos ingresados.", { field: fallbackField, code: "VALIDATION_ERROR" });
  }

  if (status === 409) {
    return new ApiError(text ?? "Ese registro ya existe o entra en conflicto con el estado actual.", {
      field: fallbackField,
      code: "CONFLICT",
    });
  }

  if (status === 429) {
    return new ApiError(text ?? "Demasiados intentos. Intenta más tarde.", { code: "RATE_LIMITED" });
  }

  if (status === 401) {
    return new ApiError("Tu sesión no es válida o expiró. Vuelve a iniciar sesión.", { code: "UNAUTHORIZED" });
  }

  if (status === 403) {
    return new ApiError(text ?? "No tienes permisos para esta acción.", { code: "FORBIDDEN" });
  }

  if (status === 404) {
    return new ApiError(text ?? "No se encontró el recurso solicitado.", { code: "NOT_FOUND" });
  }

  if (status === 400) {
    return new ApiError(text ?? "Solicitud inválida.", { field: fallbackField, code: "BAD_REQUEST" });
  }

  return new ApiError(text ?? "Ocurrió un error inesperado. Intenta nuevamente.", { code: "UNKNOWN" });
}

export function createApiClient(baseUrl: string, customMapError?: ErrorMapper) {
  const API_BASE = baseUrl.replace(/\/$/, "");

  function toApiError(status: number, detail: unknown, fallbackField?: string): ApiError {
    return customMapError?.(status, detail, fallbackField) ?? defaultMapError(status, detail, fallbackField);
  }

  async function request<T>(path: string, init: RequestInit & { fallbackField?: string } = {}): Promise<T> {
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

  return { request, authHeaders, API_BASE };
}
