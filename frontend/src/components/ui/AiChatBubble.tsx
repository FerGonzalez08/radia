// Burbuja flotante del agente de orientación académica (IA).
// Conectada al microservicio real del agente (ver services/agenteOrientacionApi.ts).
// Comparte la conversación con la página /app/orientacion vía OrientacionContext.
import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Bot, Maximize2, MessageCircle, X } from "lucide-react";
import { OrientacionChat } from "../../features/orientacion/OrientacionChat";
import styles from "./AiChatBubble.module.css";

export function AiChatBubble() {
  const [open, setOpen] = useState(false);
  const { pathname } = useLocation();

  // En la página completa del agente la burbuja sobra.
  if (pathname.startsWith("/app/orientacion")) return null;

  return (
    <>
      {open && (
        <div className={styles.panel} role="dialog" aria-label="Agente de orientación académica">
          <div className={styles.panelHeader}>
            <span className={styles.panelTitle}>
              <Bot size={16} /> Orientación académica · IA
            </span>
            <span className={styles.panelActions}>
              <Link
                to="/app/orientacion"
                className={styles.panelClose}
                onClick={() => setOpen(false)}
                aria-label="Abrir en pantalla completa"
                title="Abrir en pantalla completa"
              >
                <Maximize2 size={14} />
              </Link>
              <button className={styles.panelClose} onClick={() => setOpen(false)} aria-label="Cerrar">
                <X size={16} />
              </button>
            </span>
          </div>
          <div className={styles.panelChat}>
            <OrientacionChat compact />
          </div>
        </div>
      )}

      <button
        type="button"
        className={styles.fab}
        onClick={() => setOpen((v) => !v)}
        aria-label={open ? "Cerrar agente de orientación" : "Abrir agente de orientación"}
        aria-expanded={open}
      >
        {open ? <X size={22} /> : <MessageCircle size={22} />}
      </button>
    </>
  );
}
