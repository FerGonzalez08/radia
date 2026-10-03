// Caché local de nombres de contraparte (mentor <-> mentee), alimentada por
// resultados de búsqueda de mentoras y por el momento de solicitar una
// mentoría. Existe porque navigation-service y chat-service identifican a
// las personas por user_id (UUID) y ninguno de los cuatro microservicios
// expone hoy un endpoint de "perfil público por id" para un rol no admin —
// solo GET /roles/users (role-service) lo tiene, y es exclusivo de admin.
// Mientras ese endpoint no exista, esta caché evita mostrar UUIDs crudos en
// el chat y en "Mis mentorías" para nombres que la propia sesión ya vio.
const KEY = "radia.peerNames.v1";

function readCache(): Record<string, string> {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as Record<string, string>) : {};
  } catch {
    return {};
  }
}

function writeCache(cache: Record<string, string>) {
  try {
    localStorage.setItem(KEY, JSON.stringify(cache));
  } catch {
    // localStorage no disponible (modo privado, cuota llena, etc.) — no crítico.
  }
}

export function cachePeerName(userId: string, nombre: string) {
  if (!userId || !nombre) return;
  const cache = readCache();
  if (cache[userId] === nombre) return;
  cache[userId] = nombre;
  writeCache(cache);
}

export function cachePeerNames(entries: Array<{ id: string; nombre: string }>) {
  const cache = readCache();
  let changed = false;
  for (const { id, nombre } of entries) {
    if (id && nombre && cache[id] !== nombre) {
      cache[id] = nombre;
      changed = true;
    }
  }
  if (changed) writeCache(cache);
}

/** Devuelve el nombre cacheado, o un identificador corto legible como respaldo. */
export function getPeerName(userId: string, fallbackLabel: string): string {
  const cache = readCache();
  return cache[userId] ?? `${fallbackLabel} #${userId.slice(0, 4).toUpperCase()}`;
}

export function hasPeerName(userId: string): boolean {
  return Boolean(readCache()[userId]);
}

// --- Caché de horario por mentoría (mismo motivo: MentorshipOut no trae el
// detalle del bloque de disponibilidad, solo su id) -----------------------
export interface CachedSlotInfo {
  fecha: string;
  horaInicio: string;
  horaFin: string;
}

const SLOT_KEY = "radia.mentorshipSlots.v1";

function readSlotCache(): Record<string, CachedSlotInfo> {
  try {
    const raw = localStorage.getItem(SLOT_KEY);
    return raw ? (JSON.parse(raw) as Record<string, CachedSlotInfo>) : {};
  } catch {
    return {};
  }
}

export function cacheMentorshipSlot(mentorshipId: string, slot: CachedSlotInfo) {
  const cache = readSlotCache();
  cache[mentorshipId] = slot;
  try {
    localStorage.setItem(SLOT_KEY, JSON.stringify(cache));
  } catch {
    // no crítico
  }
}

export function getMentorshipSlot(mentorshipId: string): CachedSlotInfo | undefined {
  return readSlotCache()[mentorshipId];
}
