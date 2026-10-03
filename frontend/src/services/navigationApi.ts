// Cliente HTTP de navigation-service (FastAPI, puerto 8003 en local — ver
// docker-compose.yml del repo de backend). Cubre el catálogo de categorías
// (RQF-024), la selección de categorías de la mentora (RQF-031), la
// búsqueda de mentoras (RQF-027), su disponibilidad (RQF-025) y el ciclo de
// vida de una mentoría: solicitud (RQF-028), aceptar/rechazar (RQF-029) y
// cancelación.
import type {
  AvailabilitySlot,
  Category,
  Mentorship,
  MentorSearchResult,
  MentorSettings,
} from "../types";
import { createApiClient } from "./httpClient";

const API_URL = (import.meta.env.VITE_NAV_API_URL ?? "http://localhost:8003").replace(/\/$/, "");
const { request, authHeaders } = createApiClient(API_URL);

interface CategoryOut {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
}

interface MentorSearchResultOut {
  mentor_user_id: string;
  nombre: string;
  email: string;
  categories: string[];
}

interface AvailabilitySlotOut {
  id: string;
  mentor_user_id: string;
  date: string;
  start_time: string;
  end_time: string;
  status: "libre" | "reservado";
}

interface MentorshipOut {
  id: string;
  student_user_id: string;
  mentor_user_id: string;
  availability_slot_id: string;
  status: Mentorship["estado"];
  created_at: string;
  confirmed_at: string | null;
}

interface MentorSettingsOut {
  mentor_user_id: string;
  auto_accept: boolean;
  weekly_limit: number;
}

function mapCategory(c: CategoryOut): Category {
  return { id: c.id, nombre: c.name, descripcion: c.description, creadaEn: c.created_at };
}

function mapSearchResult(r: MentorSearchResultOut): MentorSearchResult {
  return { mentorUserId: r.mentor_user_id, nombre: r.nombre, correo: r.email, categorias: r.categories };
}

function mapSlot(s: AvailabilitySlotOut): AvailabilitySlot {
  return { id: s.id, mentorUserId: s.mentor_user_id, fecha: s.date, horaInicio: s.start_time, horaFin: s.end_time, estado: s.status };
}

function mapMentorship(m: MentorshipOut): Mentorship {
  return {
    id: m.id,
    estudianteId: m.student_user_id,
    mentorId: m.mentor_user_id,
    bloqueId: m.availability_slot_id,
    estado: m.status,
    creadaEn: m.created_at,
    confirmadaEn: m.confirmed_at,
  };
}

function mapSettings(s: MentorSettingsOut): MentorSettings {
  return { mentorUserId: s.mentor_user_id, autoAceptar: s.auto_accept, limiteSemanal: s.weekly_limit };
}

// --- Categorías (RQF-024, catálogo — solo administrador escribe) ----------

export async function listCategories(accessToken: string): Promise<Category[]> {
  const result = await request<CategoryOut[]>("/categories", { headers: authHeaders(accessToken) });
  return result.map(mapCategory);
}

export async function createCategory(accessToken: string, nombre: string, descripcion?: string): Promise<Category> {
  const result = await request<CategoryOut>("/categories", {
    method: "POST",
    headers: authHeaders(accessToken),
    body: JSON.stringify({ name: nombre.trim(), description: descripcion?.trim() || null }),
    fallbackField: "nombre",
  });
  return mapCategory(result);
}

export async function updateCategory(
  accessToken: string,
  categoryId: string,
  changes: { nombre?: string; descripcion?: string | null },
): Promise<Category> {
  const result = await request<CategoryOut>(`/categories/${categoryId}`, {
    method: "PUT",
    headers: authHeaders(accessToken),
    body: JSON.stringify({ name: changes.nombre?.trim(), description: changes.descripcion }),
  });
  return mapCategory(result);
}

export async function deleteCategory(accessToken: string, categoryId: string): Promise<void> {
  await request<void>(`/categories/${categoryId}`, { method: "DELETE", headers: authHeaders(accessToken) });
}

// --- Categorías propias de la mentora (RQF-031) -----------------------------

export async function getMyCategories(accessToken: string): Promise<Category[]> {
  const result = await request<CategoryOut[]>("/mentors/me/categories", { headers: authHeaders(accessToken) });
  return result.map(mapCategory);
}

export async function setMyCategories(accessToken: string, categoryIds: string[]): Promise<Category[]> {
  const result = await request<CategoryOut[]>("/mentors/me/categories", {
    method: "PUT",
    headers: authHeaders(accessToken),
    body: JSON.stringify({ category_ids: categoryIds }),
  });
  return result.map(mapCategory);
}

// --- Búsqueda de mentoras por categoría (RQF-027) --------------------------

export async function searchMentorsByCategory(accessToken: string, categoryId: string): Promise<MentorSearchResult[]> {
  const result = await request<MentorSearchResultOut[]>(`/search/mentors?category_id=${encodeURIComponent(categoryId)}`, {
    headers: authHeaders(accessToken),
  });
  return result.map(mapSearchResult);
}

// --- Configuración de aceptación de la mentora (RQF-026) -------------------

export async function getMySettings(accessToken: string): Promise<MentorSettings> {
  const result = await request<MentorSettingsOut>("/mentors/me/settings", { headers: authHeaders(accessToken) });
  return mapSettings(result);
}

export async function updateMySettings(accessToken: string, autoAceptar: boolean): Promise<MentorSettings> {
  const result = await request<MentorSettingsOut>("/mentors/me/settings", {
    method: "PUT",
    headers: authHeaders(accessToken),
    body: JSON.stringify({ auto_accept: autoAceptar }),
  });
  return mapSettings(result);
}

// --- Disponibilidad (RQF-025) ----------------------------------------------

export async function getMyAvailability(accessToken: string): Promise<AvailabilitySlot[]> {
  const result = await request<AvailabilitySlotOut[]>("/mentors/me/availability", { headers: authHeaders(accessToken) });
  return result.map(mapSlot);
}

export async function createAvailabilitySlot(
  accessToken: string,
  fecha: string,
  horaInicio: string,
  horaFin: string,
): Promise<AvailabilitySlot> {
  const result = await request<AvailabilitySlotOut>("/mentors/me/availability", {
    method: "POST",
    headers: authHeaders(accessToken),
    body: JSON.stringify({ date: fecha, start_time: horaInicio, end_time: horaFin }),
    fallbackField: "horaFin",
  });
  return mapSlot(result);
}

export async function deleteAvailabilitySlot(accessToken: string, slotId: string): Promise<void> {
  await request<void>(`/mentors/me/availability/${slotId}`, { method: "DELETE", headers: authHeaders(accessToken) });
}

/** Vista pública (para el estudiante): solo bloques libres de esa mentora. */
export async function getMentorAvailability(accessToken: string, mentorId: string): Promise<AvailabilitySlot[]> {
  const result = await request<AvailabilitySlotOut[]>(`/mentors/${mentorId}/availability`, {
    headers: authHeaders(accessToken),
  });
  return result.map(mapSlot);
}

// --- Mentorías (RQF-028, RQF-029) -------------------------------------------

export async function requestMentorship(accessToken: string, availabilitySlotId: string): Promise<Mentorship> {
  const result = await request<MentorshipOut>("/mentorships", {
    method: "POST",
    headers: authHeaders(accessToken),
    body: JSON.stringify({ availability_slot_id: availabilitySlotId }),
  });
  return mapMentorship(result);
}

export async function listMyMentorRequests(accessToken: string): Promise<Mentorship[]> {
  const result = await request<MentorshipOut[]>("/mentors/me/mentorships", { headers: authHeaders(accessToken) });
  return result.map(mapMentorship);
}

export async function listMyStudentMentorships(accessToken: string): Promise<Mentorship[]> {
  const result = await request<MentorshipOut[]>("/students/me/mentorships", { headers: authHeaders(accessToken) });
  return result.map(mapMentorship);
}

export async function acceptMentorship(accessToken: string, mentorshipId: string): Promise<Mentorship> {
  const result = await request<MentorshipOut>(`/mentorships/${mentorshipId}/accept`, {
    method: "POST",
    headers: authHeaders(accessToken),
  });
  return mapMentorship(result);
}

export async function rejectMentorship(accessToken: string, mentorshipId: string): Promise<Mentorship> {
  const result = await request<MentorshipOut>(`/mentorships/${mentorshipId}/reject`, {
    method: "POST",
    headers: authHeaders(accessToken),
  });
  return mapMentorship(result);
}

export async function cancelMentorship(accessToken: string, mentorshipId: string): Promise<Mentorship> {
  const result = await request<MentorshipOut>(`/mentorships/${mentorshipId}/cancel`, {
    method: "POST",
    headers: authHeaders(accessToken),
  });
  return mapMentorship(result);
}
