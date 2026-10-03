import { useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  Bot,
  Home,
  LogIn,
  Menu,
  MessagesSquare,
  Search,
  Sparkles,
  UserPlus,
  Users,
  X,
} from "lucide-react";
import { Logo } from "../components/ui/Logo";
import styles from "./LandingPage.module.css";

// Chatbot IA (microservicio futuro) sigue anunciado aquí porque ya tiene
// fecha de integración prevista; Foro y Cursos solo se muestran una vez
// hay sesión iniciada (ver features/navigation/menuConfig.ts).
const FEATURES = [
  {
    icon: Users,
    title: "Mentoría 1:1",
    body: "Cada mentee se conecta con una mentora que ya recorrió el camino en ingeniería, para acompañarla en su crecimiento académico y profesional.",
  },
  {
    icon: Search,
    title: "Match por categoría",
    body: "Busca mentoras por área (Python, React, bases de datos, UX/UI y más), revisa su disponibilidad real y agenda un bloque en minutos.",
  },
  {
    icon: MessagesSquare,
    title: "Chat en tiempo real",
    body: "Mensajería instantánea con confirmación de entrega, presencia en línea e historial de conversación siempre disponible.",
  },
  {
    icon: Bot,
    title: "Chatbot IA",
    body: "Un asistente conversacional que se integrará como microservicio a RADIA para resolver dudas y acompañar tu experiencia — próximamente.",
  },
];

const STATS = [
  { value: "4", label: "microservicios en producción" },
  { value: "100%", label: "verificación por correo" },
  { value: "< 1.5s", label: "entrega de mensajes p95" },
];

const STEPS = [
  { n: "01", title: "Crea tu cuenta", body: "Regístrate como mentee y verifica tu correo en minutos." },
  { n: "02", title: "Encuentra tu match", body: "Filtra mentoras por categoría y elige un bloque de disponibilidad." },
  { n: "03", title: "Empieza a conversar", body: "Usa el chat en tiempo real para dar seguimiento a tu acompañamiento." },
];

// Menú del landing: solo secciones públicas de esta misma página. Foro,
// Cursos y el resto de módulos futuros se ven en el menú una vez hay
// sesión iniciada — no tiene sentido anunciarlos antes (ver HU012).
const MENU_LINKS = [
  { label: "Inicio", icon: Home, href: "#inicio" },
  { label: "Características", icon: Sparkles, href: "#caracteristicas" },
  { label: "Cómo funciona", icon: ArrowRight, href: "#como-funciona" },
];

export default function LandingPage() {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <div className={styles.page}>
      <header className={styles.nav} id="inicio">
        <div className={styles.navInner}>
          <div className={styles.navLeft}>
            <button
              type="button"
              className={styles.menuButton}
              onClick={() => setMenuOpen(true)}
              aria-label="Abrir menú"
              aria-expanded={menuOpen}
            >
              <Menu size={20} />
            </button>
            <Logo variant="full" height={30} />
          </div>

          <nav className={styles.navActions}>
            <Link to="/iniciar-sesion" className={styles.navLink}>
              Iniciar sesión
            </Link>
            <Link to="/registro" className={styles.navCta}>
              Crear cuenta
            </Link>
          </nav>
        </div>
      </header>

      {menuOpen && (
        <>
          <div className={styles.menuBackdrop} onClick={() => setMenuOpen(false)} aria-hidden />
          <aside className={styles.menuPanel}>
            <div className={styles.menuHeader}>
              <Logo variant="full-white" height={26} />
              <button
                type="button"
                className={styles.menuClose}
                onClick={() => setMenuOpen(false)}
                aria-label="Cerrar menú"
              >
                <X size={20} />
              </button>
            </div>

            <nav className={styles.menuList}>
              {MENU_LINKS.map((item) => {
                const Icon = item.icon;
                return (
                  <a key={item.label} href={item.href} className={styles.menuItem} onClick={() => setMenuOpen(false)}>
                    <Icon size={18} />
                    <span>{item.label}</span>
                  </a>
                );
              })}
            </nav>

            <div className={styles.menuFooter}>
              <Link to="/iniciar-sesion" className={styles.menuItem} onClick={() => setMenuOpen(false)}>
                <LogIn size={18} />
                <span>Iniciar sesión</span>
              </Link>
              <Link to="/registro" className={styles.menuCta} onClick={() => setMenuOpen(false)}>
                <UserPlus size={18} />
                <span>Crear cuenta</span>
              </Link>
            </div>
          </aside>
        </>
      )}

      <main>
        <section className={styles.hero}>
          <div className={styles.heroGlow} aria-hidden />
          <div className={styles.heroGrid}>
            <div className={styles.heroCopy}>
              <p className={styles.eyebrow}>
                <Sparkles size={14} /> Women Tech UCatólica
              </p>
              <h1 className={styles.heroTitle}>
                Conectamos mentees con <span className="text-gradient">mentoras</span> que ya recorrieron el camino en
                STEM.
              </h1>
              <p className={styles.heroSubtitle}>
                RADIA es la plataforma de mentoría de la comunidad Women Tech UCatólica: búsqueda por categorías,
                agendamiento de disponibilidad y conversación en tiempo real en una sola red.
              </p>
              <div className={styles.heroActions}>
                <Link to="/registro" className={styles.primaryCta}>
                  Crear cuenta gratis <ArrowRight size={16} />
                </Link>
                <Link to="/iniciar-sesion" className={styles.secondaryCta}>
                  Ya tengo cuenta
                </Link>
              </div>
            </div>

            <div className={styles.heroVisual} aria-hidden="true">
              <div className={styles.mockCard}>
                <div className={styles.mockCardHeader}>
                  <span className={styles.mockDot} />
                  <span className={styles.mockDot} />
                  <span className={styles.mockDot} />
                  <span className={styles.mockCardTitle}>Chat RADIA</span>
                </div>
                <div className={styles.mockChat}>
                  <div className={[styles.mockBubble, styles.mockBubbleIn].join(" ")}>
                    ¡Hola! Vi tu perfil, ¿en qué semestre vas?
                  </div>
                  <div className={[styles.mockBubble, styles.mockBubbleOut].join(" ")}>
                    7° de Ing. de Sistemas, quiero reforzar bases de datos 🙌
                  </div>
                  <div className={styles.mockTyping}>
                    <span />
                    <span />
                    <span />
                  </div>
                </div>
              </div>
              <div className={styles.mockBadge}>
                <Search size={13} /> Match por categoría
              </div>
            </div>
          </div>
        </section>

        <section className={styles.stats}>
          {STATS.map((s) => (
            <div className={styles.statItem} key={s.label}>
              <p className={styles.statValue}>{s.value}</p>
              <p className={styles.statLabel}>{s.label}</p>
            </div>
          ))}
        </section>

        <section className={styles.features} id="caracteristicas">
          {FEATURES.map((f) => (
            <div className={styles.featureCard} key={f.title}>
              <span className={styles.featureIcon}>
                <f.icon size={19} />
              </span>
              <h3>{f.title}</h3>
              <p>{f.body}</p>
            </div>
          ))}
        </section>

        <section className={styles.steps} id="como-funciona">
          <p className={styles.eyebrow} style={{ marginBottom: 8 }}>
            Cómo funciona
          </p>
          <h2 className={styles.stepsTitle}>Empezar toma menos de cinco minutos.</h2>
          <div className={styles.stepsGrid}>
            {STEPS.map((s) => (
              <div className={styles.stepCard} key={s.n}>
                <span className={styles.stepNumber}>{s.n}</span>
                <h3>{s.title}</h3>
                <p>{s.body}</p>
              </div>
            ))}
          </div>
        </section>

        <section className={styles.closing}>
          <h2>¿Todo listo para empezar tu mentoría?</h2>
          <p>Únete a la comunidad RADIA y da el siguiente paso en tu camino en ingeniería.</p>
          <Link to="/registro" className={styles.primaryCta}>
            Crear cuenta gratis <ArrowRight size={16} />
          </Link>
        </section>
      </main>

      <footer className={styles.footer}>
        <Logo variant="full" height={22} />
        <p>Trabajo de Grado · Ingeniería de Sistemas y Computación · Universidad Católica de Colombia</p>
      </footer>
    </div>
  );
}
