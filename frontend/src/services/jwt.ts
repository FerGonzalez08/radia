// Utilidades de lectura del JWT del auth-service real (HU004).
// El access token lo emite y firma el backend (HS256) — aquí solo se
// decodifica el payload en el cliente para leer su expiración y decidir
// cuándo pedir uno nuevo con /auth/refresh; la firma nunca se verifica en
// el navegador (no tendría sentido: el cliente no tiene el secreto).

export interface RadiaTokenPayload {
  sub: string; // user id
  role_id: string;
  iat: number; // epoch segundos
  exp: number; // epoch segundos
}

function base64UrlDecode(input: string): string {
  const padded = input.replace(/-/g, "+").replace(/_/g, "/").padEnd(input.length + ((4 - (input.length % 4)) % 4), "=");
  return decodeURIComponent(escape(atob(padded)));
}

export function decodeToken(token: string | null): RadiaTokenPayload | null {
  if (!token) return null;
  const parts = token.split(".");
  if (parts.length !== 3) return null;
  try {
    return JSON.parse(base64UrlDecode(parts[1])) as RadiaTokenPayload;
  } catch {
    return null;
  }
}

export function isTokenExpired(token: string | null): boolean {
  const payload = decodeToken(token);
  if (!payload) return true;
  return Date.now() >= payload.exp * 1000;
}

/** HU004 - Escenario 4: renovar automáticamente si está cerca de expirar. */
export function shouldRenew(token: string | null, thresholdMs = 2 * 60 * 1000): boolean {
  const payload = decodeToken(token);
  if (!payload) return false;
  return payload.exp * 1000 - Date.now() <= thresholdMs;
}
