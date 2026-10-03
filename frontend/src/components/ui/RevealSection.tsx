import { useEffect, useRef, useState, type ReactNode } from "react";
import styles from "./RevealSection.module.css";

interface RevealSectionProps {
  // Render-prop: expone `visible` para que el contenido interno pueda
  // escalonar su propia animacion (ver listas de LandingPage/DashboardPage)
  // sin depender de selectores CSS entre modulos distintos.
  children: (visible: boolean) => ReactNode;
  className?: string;
  id?: string;
}

// Anima la seccion completa (fade + slide-up) la primera vez que entra en
// el viewport, con IntersectionObserver -- se desconecta apenas se dispara
// una vez, no vuelve a animar si el usuario sube y baja la pagina.
export function RevealSection({ children, className, id }: RevealSectionProps) {
  const ref = useRef<HTMLElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    if (typeof IntersectionObserver === "undefined") {
      setVisible(true);
      return;
    }
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.12, rootMargin: "0px 0px -60px 0px" },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  return (
    <section
      ref={ref}
      id={id}
      className={[styles.reveal, visible ? styles.visible : "", className ?? ""].filter(Boolean).join(" ")}
    >
      {children(visible)}
    </section>
  );
}
