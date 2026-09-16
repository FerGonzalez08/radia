/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** URL base del auth-service real (ver services/auth-service en el repo del backend). */
  readonly VITE_API_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
