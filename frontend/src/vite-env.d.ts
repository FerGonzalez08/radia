/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** URL base de auth-service (ver services/auth-service en el repo del backend). */
  readonly VITE_API_URL?: string;
  /** URL base de role-service. */
  readonly VITE_ROLE_API_URL?: string;
  /** URL base de navigation-service. */
  readonly VITE_NAV_API_URL?: string;
  /** URL base de chat-service (también se deriva de aquí la URL del websocket). */
  readonly VITE_CHAT_API_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
