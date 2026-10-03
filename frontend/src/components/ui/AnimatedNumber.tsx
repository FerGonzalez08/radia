import { useEffect, useRef, useState } from "react";

interface AnimatedNumberProps {
  value: number;
  active: boolean;
  duration?: number;
  format?: (n: number) => string;
}

// Cuenta de 0 al valor final cuando `active` pasa a true (lo controla el
// padre via RevealSection, para no montar un segundo IntersectionObserver).
// Respeta prefers-reduced-motion mostrando el valor final de una vez.
export function AnimatedNumber({ value, active, duration = 900, format }: AnimatedNumberProps) {
  const [display, setDisplay] = useState(0);
  const started = useRef(false);

  useEffect(() => {
    if (!active || started.current) return;
    started.current = true;

    const reduceMotion =
      typeof window !== "undefined" && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    if (reduceMotion) {
      setDisplay(value);
      return;
    }

    const start = performance.now();
    let raf = 0;
    const tick = (now: number) => {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(value * eased);
      if (progress < 1) {
        raf = requestAnimationFrame(tick);
      } else {
        setDisplay(value);
      }
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [active, value, duration]);

  const shown = format ? format(display) : Math.round(display).toString();
  return <>{shown}</>;
}
