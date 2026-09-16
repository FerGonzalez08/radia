// Tipos compartidos del módulo core de RADIA (auth, roles, navegación, chat).
// El auth (HU001-HU006) ya habla con el auth-service real (FastAPI) del
// repo de backend — ver src/services/api.ts. El chat (HU016-HU019) sigue
// simulado en el cliente porque ese microservicio aún no existe.

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
