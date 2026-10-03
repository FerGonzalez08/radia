import fullColor from "../../assets/img/radia-full.png";
import fullWhite from "../../assets/img/radia-full-white.png";
import isotipo from "../../assets/img/radia-isotipo.png";
import styles from "./Logo.module.css";

interface LogoProps {
  variant?: "full" | "full-white" | "isotipo";
  height?: number;
  className?: string;
}

/**
 * Manual de marca §5 "Uso sobre fondos": la versión a color se usa sobre
 * blanco/neutro claro; sobre fondos oscuros o el propio degradado se usa
 * la versión completamente blanca (la tagline negra "no funciona sobre
 * fondo oscuro").
 */
export function Logo({ variant = "full", height = 40, className }: LogoProps) {
  const src = variant === "full" ? fullColor : variant === "full-white" ? fullWhite : isotipo;
  return (
    <img
      src={src}
      alt="RADIA — Empowering Women in STEM"
      height={height}
      className={[styles.logo, className ?? ""].join(" ")}
      style={{ height }}
    />
  );
}
