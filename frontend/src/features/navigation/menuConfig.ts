// HU012 - Menú dinámico por rol.
// Cada rol ve únicamente las secciones habilitadas para él; HU014 usa esta
// misma fuente de verdad para bloquear el acceso directo por URL.
import type { LucideIcon } from "lucide-react";
import { Home, MessagesSquare, ShieldCheck, User, Users } from "lucide-react";
import type { Role } from "../../types";

export interface MenuItem {
  path: string;
  label: string;
  icon: LucideIcon;
  /** Para HU013: qué rutas hijas también resaltan esta sección. */
  matchPrefixes?: string[];
}

const MENUS: Record<Role, MenuItem[]> = {
  mentee: [
    { path: "/app/inicio", label: "Inicio", icon: Home },
    { path: "/app/chat", label: "Chat con mi mentora", icon: MessagesSquare, matchPrefixes: ["/app/chat"] },
    { path: "/app/perfil", label: "Mi perfil", icon: User },
  ],
  mentor: [
    { path: "/app/inicio", label: "Inicio", icon: Home },
    { path: "/app/chat", label: "Mis mentees", icon: MessagesSquare, matchPrefixes: ["/app/chat"] },
    { path: "/app/perfil", label: "Mi perfil", icon: User },
  ],
  admin: [
    { path: "/app/inicio", label: "Inicio", icon: Home },
    { path: "/app/usuarias", label: "Usuarias y roles", icon: Users },
    { path: "/app/chat", label: "Chat", icon: MessagesSquare, matchPrefixes: ["/app/chat"] },
    { path: "/app/permisos", label: "Matriz de permisos", icon: ShieldCheck },
    { path: "/app/perfil", label: "Mi perfil", icon: User },
  ],
};

/** HU012 - Escenario 3: si no se puede determinar el rol, menú mínimo de solo lectura. */
export const FALLBACK_MENU: MenuItem[] = [{ path: "/app/inicio", label: "Inicio", icon: Home }];

export function getMenuForRole(role: Role | null | undefined): MenuItem[] {
  if (!role || !MENUS[role]) return FALLBACK_MENU;
  return MENUS[role];
}

export const ROLE_LABEL: Record<Role, string> = {
  mentee: "Mentee",
  mentor: "Mentora",
  admin: "Administradora",
};

/** HU014 - rutas cuyo acceso está restringido a ciertos roles. */
export const ROUTE_ROLES: Record<string, Role[]> = {
  "/app/usuarias": ["admin"],
  "/app/permisos": ["admin"],
};
