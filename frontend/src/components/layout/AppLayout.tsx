import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { LogOut, Menu, X } from "lucide-react";
import { Logo } from "../ui/Logo";
import { useAuth } from "../../context/AuthContext";
import { getMenuForRole, ROLE_LABEL } from "../../features/navigation/menuConfig";
import styles from "./AppLayout.module.css";

const MOBILE_BREAKPOINT = 768; // HU015

function initials(name: string): string {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase())
    .join("");
}

export function AppLayout() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(
    typeof window !== "undefined" ? window.innerWidth < MOBILE_BREAKPOINT : false,
  );

  // HU015 - Escenario 3: al cruzar el umbral de 768px se cambia de formato
  // sin recargar la página.
  useEffect(() => {
    const mql = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT - 1}px)`);
    const onChange = (e: MediaQueryListEvent) => {
      setIsMobile(e.matches);
      if (!e.matches) setMobileOpen(false);
    };
    mql.addEventListener("change", onChange);
    return () => mql.removeEventListener("change", onChange);
  }, []);

  // Cierra el drawer móvil en cada cambio de ruta (HU015 - Escenario 2).
  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  const menu = getMenuForRole(user?.rol);

  return (
    <div className={styles.shell}>
      <header className={styles.topbar}>
        <button
          className={styles.hamburger}
          onClick={() => setMobileOpen((v) => !v)}
          aria-label={mobileOpen ? "Cerrar menú" : "Abrir menú"}
          aria-expanded={mobileOpen}
        >
          {mobileOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
        <Logo variant="full-white" height={26} />
        <div className={styles.topbarUser}>
          {user && (
            <>
              <span className={styles.avatar} style={{ background: user.avatarColor }}>
                {initials(user.nombre)}
              </span>
            </>
          )}
        </div>
      </header>

      {isMobile && mobileOpen && <div className={styles.backdrop} onClick={() => setMobileOpen(false)} />}

      <aside className={[styles.sidebar, isMobile ? styles.sidebarMobile : "", mobileOpen ? styles.sidebarOpen : ""].join(" ")}>
        <div className={styles.sidebarHeader}>
          <Logo variant="full-white" height={30} />
        </div>

        <nav className={styles.nav}>
          <ul>
            {menu.map((item) => {
              const Icon = item.icon;

              // Módulos futuros (HU futuras, fuera del núcleo de esta entrega):
              // se muestran para dar visibilidad del alcance completo de RADIA,
              // pero todavía no navegan a ningún microservicio real.
              if (item.disabled) {
                return (
                  <li key={item.path}>
                    <span className={[styles.navItem, styles.navItemDisabled].join(" ")} aria-disabled="true">
                      <Icon size={18} />
                      <span>{item.label}</span>
                      <span className={styles.comingSoon}>Pronto</span>
                    </span>
                  </li>
                );
              }

              const prefixes = item.matchPrefixes ?? [item.path];
              const active = prefixes.some((p) => location.pathname.startsWith(p));
              return (
                <li key={item.path}>
                  <NavLink to={item.path} className={() => [styles.navItem, active ? styles.navItemActive : ""].join(" ")}>
                    <Icon size={18} />
                    <span>{item.label}</span>
                  </NavLink>
                </li>
              );
            })}
          </ul>
        </nav>

        {user && (
          <div className={styles.sidebarFooter}>
            <div className={styles.userCard}>
              <span className={styles.avatar} style={{ background: user.avatarColor }}>
                {initials(user.nombre)}
              </span>
              <div className={styles.userMeta}>
                <p className={styles.userName}>{user.nombre}</p>
                <p className={styles.userRole}>{ROLE_LABEL[user.rol]}</p>
              </div>
            </div>
            <button className={styles.logoutBtn} onClick={() => logout()}>
              <LogOut size={16} /> Cerrar sesión
            </button>
          </div>
        )}
      </aside>

      <main className={styles.content}>
        <Outlet />
      </main>
    </div>
  );
}
