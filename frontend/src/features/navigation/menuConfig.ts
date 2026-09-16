// HU012 - Menú dinámico por rol.
// Cada rol ve únicamente las secciones habilitadas para él; HU014 usa esta
// misma fuente de verdad para bloquear el acceso directo por URL.
import type { LucideIcon } from "lucide-react";
import { Bot, BookOpen, Home, Megaphone, MessagesSquare, ShieldCheck, User, Users } from "lucide-react";
import type { Role } from "../../types";

export interface MenuItem {
  path: string;
  label: string;
  icon: LucideIcon;
  /** Para HU013: qué rutas hijas también resaltan esta sección. */
  matchPrefixes?: string[];
  /**
   * Secciones de módulos futuros de RADIA (agente de IA, foro, biblioteca de
   * recursos) que todavía no existen como microservicio. Se muestran en el
   * menú para dar visibilidad del alcance completo de la plataforma, pero no
   * navegan a ningún lado todavía.
   */
  disabled?: boolean;
}

/** Módulos futuros, visibles para cualquier rol autenticado. */
const UPCOMING_ITEMS: MenuItem[] = [
  { path: "/app/chatbot", label: "Chatbot IA", icon: Bot, disabled: true },
  { path: "/app/foro", label: "Foro", icon: Megaphone, disabled: true },
  { path: "/app/cursos", label: "Cursos", icon: BookOpen, disabled: true },
];

const MENUS: Record<Role, MenuItem[]> = {
  mentee: [
    { path: "/app/inicio", label: "Inicio", icon: Home },
    { path: "/app/chat", label: "Chat con mi mentor", icon: MessagesSquare, matchPrefixes: ["/app/chat"] },
    { path: "/app/perfil", label: "Mi perfil", icon: User },
    ...UPCOMING_ITEMS,
  ],
  mentor: [
    { path: "/app/inicio", label: "Inicio", icon: Home },
    { path: "/app/chat", label: "Mis mentees", icon: MessagesSquare, matchPrefixes: ["/app/chat"] },
    { path: "/app/perfil", label: "Mi perfil", icon: User },
    ...UPCOMING_ITEMS,
  ],
  admin: [
    { path: "/app/inicio", label: "Inicio", icon: Home },
    { path: "/app/usuarias", label: "Usuarios y roles", icon: Users },
    { path: "/app/chat", label: "Chat", icon: MessagesSquare, matchPrefixes: ["/app/chat"] },
    { path: "/app/permisos", label: "Matriz de permisos", icon: ShieldCheck },
    { path: "/app/perfil", label: "Mi perfil", icon: User },
    ...UPCOMING_ITEMS,
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
  mentor: "Mentor",
  admin: "Administrador",
};

/** HU014 - rutas cuyo acceso está restringido a ciertos roles. */
export const ROUTE_ROLES: Record<string, Role[]> = {
  "/app/usuarias": ["admin"],
  "/app/permisos": ["admin"],
};
