import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Bot, BookOpen, Home, LogIn, Megaphone, Menu, MessagesSquare, Sparkles, UserPlus, Users, X } from "lucide-react";
import { Logo } from "../components/ui/Logo";
import styles from "./LandingPage.module.css";

const FEATURES = [
  {
    icon: Users,
    title: "Mentoría 1:1",
    body: "Cada mentee se conecta con un mentor que ya recorrió el camino en ingeniería, para acompañarlo en su crecimiento académico y profesional.",
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

const STEPS = [
  { n: "01", title: "Crea tu cuenta", body: "Regístrate como mentee o mentor y verifica tu correo en minutos." },
  { n: "02", title: "Te conectamos", body: "Te asignamos con la contraparte adecuada dentro de la comunidad RADIA." },
  { n: "03", title: "Empieza a conversar", body: "Usa el chat para dar seguimiento al acompañamiento en tiempo real." },
];

// Vista previa del alcance completo de RADIA (núcleo + módulos futuros) para
// quien todavía no inicia sesión. Los módulos futuros solo se muestran, no
// navegan a ningún lado todavía.
const MENU_LINKS = [
  { label: "Inicio", icon: Home, href: "#inicio" },
  { label: "Chatbot IA", icon: Bot, disabled: true },
  { label: "Foro", icon: Megaphone, disabled: true },
  { label: "Cursos", icon: BookOpen, disabled: true },
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
                if (item.disabled) {
                  return (
                    <span key={item.label} className={[styles.menuItem, styles.menuItemDisabled].join(" ")} aria-disabled="true">
                      <Icon size={18} />
                      <span>{item.label}</span>
                      <span className={styles.menuBadge}>Pronto</span>
                    </span>
                  );
                }
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
          <p className={styles.eyebrow}>
            <Sparkles size={14} /> Women Tech UCatólica
          </p>
          <h1 className={styles.heroTitle}>
            Conectamos mentees con <span className="text-gradient">mentores</span> que ya recorrieron el camino en STEM.
          </h1>
          <p className={styles.heroSubtitle}>
            RADIA es la plataforma de mentoría de la comunidad Women Tech UCatólica: acompañamiento cercano,
            conversación en tiempo real y una red construida por y para mujeres en ingeniería.
          </p>
          <div className={styles.heroActions}>
            <Link to="/registro" className={styles.primaryCta}>
              Crear cuenta gratis <ArrowRight size={16} />
            </Link>
            <Link to="/iniciar-sesion" className={styles.secondaryCta}>
              Ya tengo cuenta
            </Link>
          </div>
        </section>

        <section className={styles.features}>
          {FEATURES.map((f) => (
            <div className={styles.featureCard} key={f.title}>
              <f.icon size={20} />
              <h3>{f.title}</h3>
              <p>{f.body}</p>
            </div>
          ))}
        </section>

        <section className={styles.steps}>
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
