// Tipos compartidos del módulo core de RADIA (auth, roles, navegación, chat).
// Los cuatro microservicios reales del backend ya están integrados:
// auth-service (src/services/api.ts), role-service (roleApi.ts),
// navigation-service (navigationApi.ts) y chat-service (chatApi.ts).

export type Role = "mentee" | "mentor" | "admin";

export type AccountStatus = "pendiente" | "activo" | "bloqueado";

export type Sexo = "femenino" | "masculino" | "prefiero_no_decir";

export interface User {
  id: string;
  nombre: string;
  correo: string;
  telefono: string;
  sexo: Sexo;
  fechaNacimiento: string; // ISO yyyy-mm-dd
  rol: Role;
  estado: AccountStatus;
  avatarColor: string;
  creadoEn: string;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
}

// El registro público solo crea cuentas "mentee": el auth-service real no
// acepta un campo de rol en /auth/register (siempre asigna el rol mentee
// por defecto). Una mentora se habilita después, por una administradora,
// vía PATCH /auth/admin/users/{id}/role.
export interface RegisterPayload {
  nombre: string;
  correo: string;
  password: string;
  telefono: string;
  sexo: Sexo;
  fechaNacimiento: string;
  aceptaTerminos: boolean;
}

export interface LoginPayload {
  correo: string;
  password: string;
}

export type MessageStatus = "pendiente" | "enviado" | "entregado" | "error";

export interface ChatMessage {
  id: string;
  conversationId: string;
  autorId: string;
  texto: string;
  enviadoEn: string; // ISO
  status: MessageStatus;
}

export interface ConversationParticipant {
  id: string;
  nombre: string;
  rol: Role;
  enLinea: boolean;
  ultimaConexion: string; // ISO
  avatarColor: string;
}

export interface Conversation {
  id: string;
  participante: ConversationParticipant;
  mensajes: ChatMessage[];
  noLeidos: number;
  mensajeBienvenida?: string;
}

export type SocketConnectionState = "conectado" | "conectando" | "reconectando" | "desconectado";

export interface ApiError {
  message: string;
  field?: string;
  code?: string;
}


// --- Administración de roles (role-service) --------------------------------
// role-service devuelve menos campos que auth-service (sin teléfono, sexo,
// fecha de nacimiento ni fecha de creación) — fila liviana para la tabla de
// Usuarios y roles.
export interface AdminUserRow {
  id: string;
  nombre: string;
  correo: string;
  rol: Role;
  estado: AccountStatus;
  avatarColor: string;
}

// --- Auditoría de cambios de rol (role-service) -----------------------------
// Traza de cada promoción/reversión mentee <-> mentor hecha por un
// administrador, para el panel de "Mi perfil" del administrador.
export interface RoleAuditEntry {
  id: string;
  fecha: string;
  adminNombre: string;
  adminCorreo: string;
  usuarioNombre: string;
  usuarioCorreo: string;
  rolAnterior: string;
  rolNuevo: string;
}

// --- Categorías y búsqueda de mentoras (navigation-service) ----------------

export interface Category {
  id: string;
  nombre: string;
  descripcion: string | null;
  creadaEn: string;
}

export interface MentorSearchResult {
  mentorUserId: string;
  nombre: string;
  correo: string;
  categorias: string[];
}

// --- Disponibilidad y mentorías (navigation-service) -----------------------

export type SlotStatus = "libre" | "reservado";

export interface AvailabilitySlot {
  id: string;
  mentorUserId: string;
  fecha: string; // yyyy-mm-dd
  horaInicio: string; // HH:MM[:SS]
  horaFin: string;
  estado: SlotStatus;
}

export type MentorshipStatus = "pendiente" | "confirmada" | "rechazada" | "cancelada" | "completada";

export interface Mentorship {
  id: string;
  estudianteId: string;
  mentorId: string;
  bloqueId: string;
  estado: MentorshipStatus;
  creadaEn: string;
  confirmadaEn: string | null;
}

export interface MentorSettings {
  mentorUserId: string;
  autoAceptar: boolean;
  limiteSemanal: number;
}
