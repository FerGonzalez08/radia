import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { Logo } from "../ui/Logo";
import styles from "./AuthLayout.module.css";

interface AuthLayoutProps {
  children: ReactNode;
  title: string;
  subtitle?: string;
  eyebrow?: string;
  footer?: ReactNode;
}

const HIGHLIGHTS = [
  "Mentoría 1:1 entre estudiantes y profesionales de ingeniería.",
  "Chat en tiempo real, roles y navegación pensados para el acompañamiento.",
  "Un espacio construido por y para mujeres en STEM.",
];

export function AuthLayout({ children, title, subtitle, eyebrow, footer }: AuthLayoutProps) {
  return (
    <div className={styles.page}>
      <aside className={styles.brandPanel}>
        <div className={styles.brandGlow} aria-hidden />
        <Link to="/" className={styles.brandLogo}>
          <Logo variant="full-white" height={38} />
        </Link>

        <div className={styles.brandCopy}>
          <p className={styles.brandKicker}>Women Tech UCatólica</p>
          <h1 className={styles.brandTitle}>
            Conectamos mentees con mentoras que ya recorrieron el camino en STEM.
          </h1>
          <ul className={styles.brandList}>
            {HIGHLIGHTS.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <p className={styles.brandFoot}>Trabajo de Grado · Ingeniería de Sistemas y Computación</p>
      </aside>

      <main className={styles.formPanel}>
        <div className={styles.formCard}>
          <div className={styles.mobileLogo}>
            <Logo variant="full" height={32} />
          </div>
          {eyebrow && <p className={styles.eyebrow}>{eyebrow}</p>}
          <h2 className={styles.title}>{title}</h2>
          {subtitle && <p className={styles.subtitle}>{subtitle}</p>}
          <div className={styles.content}>{children}</div>
          {footer && <div className={styles.footer}>{footer}</div>}
        </div>
      </main>
    </div>
  );
}
