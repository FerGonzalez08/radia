import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Home, LogIn, Menu, Sparkles, UserPlus, X } from "lucide-react";
import { Logo } from "../components/ui/Logo";
import { RevealSection } from "../components/ui/RevealSection";
import { AnimatedNumber } from "../components/ui/AnimatedNumber";
import styles from "./LandingPage.module.css";

// Chatbot IA (microservicio futuro) sigue anunciado aqui porque ya tiene
// fecha de integracion prevista; Foro y Cursos solo se muestran una vez
// hay sesion iniciada (ver features/navigation/menuConfig.ts).
const FEATURES = [
  {
    code: "F1",
    eyebrow: "Acompanamiento",
    title: "Mentoria 1:1",
    body: "Cada mentee se conecta con una mentora que ya recorrio el camino en ingenieria, para acompanarla en su crecimiento academico y profesional.",
  },
  {
    code: "F2",
    eyebrow: "Busqueda",
    title: "Match por categoria",
    body: "Busca mentoras por area (Python, React, bases de datos, UX/UI y mas), revisa su disponibilidad real y agenda un bloque en minutos.",
  },
  {
    code: "F3",
    eyebrow: "Conversacion",
    title: "Chat en tiempo real",
    body: "Mensajeria instantanea con confirmacion de entrega, presencia en linea e historial de conversacion siempre disponible.",
  },
  {
    code: "F4",
    eyebrow: "Proximamente",
    title: "Chatbot IA",
    body: "Un asistente conversacional que pronto estara disponible en RADIA para resolver dudas y acompanar tu experiencia.",
  },
];

// Valores numericos puros + formato, para poder animar el conteo cuando la
// seccion entra en el viewport (antes eran strings fijos).
const STATS = [
  { value: 300, format: (n: number) => `${Math.round(n)}+`, label: "mentees conectadas" },
  { value: 60, format: (n: number) => `${Math.round(n)}+`, label: "mentoras acompañando" },
  { value: 1000, format: (n: number) => `${Math.round(n).toLocaleString("es-CO")}+`, label: "mensajes enviados" },
];

const STEPS = [
  { n: "01", title: "Crea tu cuenta", body: "Registrate como mentee y verifica tu correo en minutos." },
  { n: "02", title: "Encuentra tu match", body: "Filtra mentoras por categoria y elige un bloque de disponibilidad." },
  { n: "03", title: "Empieza a conversar", body: "Usa el chat en tiempo real para dar seguimiento a tu acompanamiento." },
];

// Menu del landing: solo secciones publicas de esta misma pagina. Foro,
// Cursos y el resto de modulos futuros se ven en el menu una vez hay
// sesion iniciada -- no tiene sentido anunciarlos antes (ver HU012).
const MENU_LINKS = [
  { label: "Inicio", icon: Home, href: "#inicio" },
  { label: "Caracteristicas", icon: Sparkles, href: "#caracteristicas" },
  { label: "Como funciona", icon: ArrowRight, href: "#como-funciona" },
];

function NavDivider() {
  return <span className={styles.navDivider} aria-hidden="true">|</span>;
}

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
              aria-label="Abrir menu"
              aria-expanded={menuOpen}
            >
              <Menu size={20} />
            </button>
            <Logo variant="full-white" height={26} />
          </div>

          <nav className={styles.navActions}>
            <a href="#caracteristicas" className={styles.navLink}>Caracteristicas</a>
            <NavDivider />
            <a href="#como-funciona" className={styles.navLink}>Como funciona</a>
            <NavDivider />
            <Link to="/iniciar-sesion" className={styles.navLink}>Iniciar sesion</Link>
            <Link to="/registro" className={styles.navCta}>Crear cuenta</Link>
          </nav>
        </div>
      </header>

      {menuOpen && (
        <>
          <div className={styles.menuBackdrop} onClick={() => setMenuOpen(false)} aria-hidden />
          <aside className={styles.menuPanel}>
            <div className={styles.menuHeader}>
              <Logo variant="full-white" height={26} />
              <button type="button" className={styles.menuClose} onClick={() => setMenuOpen(false)} aria-label="Cerrar menu">
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
                <span>Iniciar sesion</span>
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
        <RevealSection className={styles.hero}>
          {() => (
            <>
              <div className={styles.heroGlow} aria-hidden="true" />
              <div className={styles.heroCopy}>
                <p className={styles.eyebrow}>
                  <Sparkles size={13} /> Women Tech UCatolica
                </p>
                <h1 className={styles.heroTitle}>
                  De buscar una mentora <span className={styles.accentText}>a tener una conversacion.</span>
                </h1>
                <hr className={styles.heroRule} />
                <p className={styles.heroSubtitle}>
                  RADIA conecta mentees con mentoras que ya recorrieron el camino en ingenieria: busqueda por
                  categorias, agendamiento de disponibilidad real y conversacion en tiempo real, en una sola
                  plataforma.
                </p>
                <div className={styles.heroActions}>
                  <Link to="/registro" className={styles.primaryCta}>
                    Crear cuenta gratis <ArrowRight size={16} />
                  </Link>
                  <Link to="/iniciar-sesion" className={styles.textLink}>
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
                      Hola! Vi tu perfil, en que semestre vas?
                    </div>
                    <div className={[styles.mockBubble, styles.mockBubbleOut].join(" ")}>
                      7 de Ing. de Sistemas, quiero reforzar bases de datos
                    </div>
                    <div className={styles.mockTyping}>
                      <span />
                      <span />
                      <span />
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}
        </RevealSection>

        <RevealSection className={styles.stats}>
          {(visible) => (
            <div className={styles.statsBox}>
              {STATS.map((s, i) => (
                <div
                  className={[styles.statRow, visible ? styles.statRowIn : ""].join(" ")}
                  key={s.label}
                  style={{ transitionDelay: `${i * 90}ms` }}
                >
                  <p className={styles.statValue}>
                    <AnimatedNumber value={s.value} active={visible} format={s.format} />
                  </p>
                  <p className={styles.statLabel}>{s.label}</p>
                </div>
              ))}
            </div>
          )}
        </RevealSection>

        <RevealSection className={styles.features} id="caracteristicas">
          {(visible) => (
            <>
              <p className={styles.eyebrow}>Que incluye RADIA</p>
              <h2 className={styles.sectionTitle}>
                Todo lo que necesitas <span className={styles.accentText}>para empezar tu mentoria.</span>
              </h2>
              <div className={styles.list}>
                {FEATURES.map((f, i) => (
                  <div
                    className={[styles.listRow, visible ? styles.listRowIn : ""].join(" ")}
                    style={{ transitionDelay: `${i * 70}ms` }}
                    key={f.code}
                  >
                    <span className={styles.listCode}>{f.code}</span>
                    <div className={styles.listBody}>
                      <p className={styles.listEyebrow}>{f.eyebrow}</p>
                      <h3>{f.title}</h3>
                      <p className={styles.listText}>{f.body}</p>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </RevealSection>

        <RevealSection className={styles.steps} id="como-funciona">
          {(visible) => (
            <>
              <p className={styles.eyebrow}>Como funciona</p>
              <h2 className={styles.sectionTitle}>Empezar toma menos de cinco minutos.</h2>
              <div className={styles.list}>
                {STEPS.map((s, i) => (
                  <div
                    className={[styles.listRow, visible ? styles.listRowIn : ""].join(" ")}
                    style={{ transitionDelay: `${i * 70}ms` }}
                    key={s.n}
                  >
                    <span className={styles.listCode}>{s.n}</span>
                    <div className={styles.listBody}>
                      <h3>{s.title}</h3>
                      <p className={styles.listText}>{s.body}</p>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </RevealSection>

        <RevealSection className={styles.closing}>
          {() => (
            <>
              <div className={styles.closingGlow} aria-hidden="true" />
              <h2>Todo listo para empezar?</h2>
              <div className={styles.closingRule} />
              <p>Unete a la comunidad RADIA y da el siguiente paso en tu camino en ingenieria.</p>
              <Link to="/registro" className={styles.primaryCta}>
                Crear cuenta gratis <ArrowRight size={16} />
              </Link>
            </>
          )}
        </RevealSection>
      </main>

      <footer className={styles.footer}>
        <Logo variant="full-white" height={18} />
        <p>© 2026 RADIA. Todos los derechos reservados.</p>
      </footer>
    </div>
  );
}
