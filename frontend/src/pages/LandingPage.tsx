import { Link } from "react-router-dom";
import { ArrowRight, MessagesSquare, ShieldCheck, Sparkles, Users } from "lucide-react";
import { Logo } from "../components/ui/Logo";
import styles from "./LandingPage.module.css";

const FEATURES = [
  {
    icon: Users,
    title: "Mentoría 1:1",
    body: "Cada mentee se conecta con una mentora que ya recorrió el camino en ingeniería, para acompañarla en su crecimiento académico y profesional.",
  },
  {
    icon: MessagesSquare,
    title: "Chat en tiempo real",
    body: "Mensajería instantánea con confirmación de entrega, presencia en línea e historial de conversación siempre disponible.",
  },
  {
    icon: ShieldCheck,
    title: "Roles y seguridad",
    body: "Acceso diferenciado por rol (mentee, mentora, administradora) y control de permisos sobre cada sección de la plataforma.",
  },
];

const STEPS = [
  { n: "01", title: "Crea tu cuenta", body: "Regístrate como mentee o mentora y verifica tu correo en minutos." },
  { n: "02", title: "Te conectamos", body: "Te asignamos con la contraparte adecuada dentro de la comunidad RADIA." },
  { n: "03", title: "Empieza a conversar", body: "Usa el chat para dar seguimiento al acompañamiento en tiempo real." },
];

export default function LandingPage() {
  return (
    <div className={styles.page}>
      <header className={styles.nav}>
        <Logo variant="full" height={30} />
        <nav className={styles.navActions}>
          <Link to="/iniciar-sesion" className={styles.navLink}>
            Iniciar sesión
          </Link>
          <Link to="/registro" className={styles.navCta}>
            Crear cuenta
          </Link>
        </nav>
      </header>

      <main>
        <section className={styles.hero}>
          <div className={styles.heroGlow} aria-hidden />
          <p className={styles.eyebrow}>
            <Sparkles size={14} /> Women Tech UCatólica
          </p>
          <h1 className={styles.heroTitle}>
            Conectamos mentees con <span className="text-gradient">mentoras</span> que ya recorrieron el camino en STEM.
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
          <h2>¿Lista para empezar tu mentoría?</h2>
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
