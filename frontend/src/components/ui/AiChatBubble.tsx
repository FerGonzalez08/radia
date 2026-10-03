// Burbuja flotante de Chatbot IA (estilo widget de servicio al cliente).
// Puramente visual por ahora: el microservicio de IA todavía no existe (ver
// FEATURES en LandingPage) — al abrir solo muestra un aviso de "próximamente".
import { useState } from "react";
import { Bot, MessageCircle, Sparkles, X } from "lucide-react";
import styles from "./AiChatBubble.module.css";

export function AiChatBubble() {
  const [open, setOpen] = useState(false);

  return (
    <>
      {open && (
        <div className={styles.panel} role="dialog" aria-label="Chatbot IA">
          <div className={styles.panelHeader}>
            <span className={styles.panelTitle}>
              <Bot size={16} /> Chatbot IA
            </span>
            <button className={styles.panelClose} onClick={() => setOpen(false)} aria-label="Cerrar">
              <X size={16} />
            </button>
          </div>
          <div className={styles.panelBody}>
            <span className={styles.panelIcon}>
              <Sparkles size={22} />
            </span>
            <p className={styles.panelText}>
              El asistente conversacional de RADIA todavía no está disponible — muy pronto vas a poder resolver
              tus dudas por aquí.
            </p>
            <span className={styles.panelBadge}>Próximamente</span>
          </div>
        </div>
      )}

      <button
        type="button"
        className={styles.fab}
        onClick={() => setOpen((v) => !v)}
        aria-label={open ? "Cerrar chatbot IA" : "Abrir chatbot IA"}
        aria-expanded={open}
      >
        {open ? <X size={22} /> : <MessageCircle size={22} />}
      </button>
    </>
  );
}
