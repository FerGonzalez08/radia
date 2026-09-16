import { AlertCircle, Check, CheckCheck, Clock3 } from "lucide-react";
import type { ChatMessage } from "../../types";
import styles from "./MessageBubble.module.css";

interface MessageBubbleProps {
  message: ChatMessage;
  isOwn: boolean;
  onRetry: (id: string) => void;
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit" });
}

function StatusIcon({ status }: { status: ChatMessage["status"] }) {
  switch (status) {
    case "pendiente":
      return <Clock3 size={13} aria-label="Pendiente de envío" />;
    case "enviado":
      return <Check size={13} aria-label="Enviado" />;
    case "entregado":
      return <CheckCheck size={13} aria-label="Entregado" />;
    case "error":
      return <AlertCircle size={13} aria-label="Error al enviar" />;
  }
}

export function MessageBubble({ message, isOwn, onRetry }: MessageBubbleProps) {
  return (
    <div className={[styles.row, isOwn ? styles.own : styles.other].join(" ")}>
      <div className={[styles.bubble, isOwn ? styles.bubbleOwn : styles.bubbleOther].join(" ")}>
        <p className={styles.text}>{message.texto}</p>
        <div className={styles.meta}>
          <span>{formatTime(message.enviadoEn)}</span>
          {isOwn && (
            <span className={[styles.status, message.status === "error" ? styles.statusError : ""].join(" ")}>
              <StatusIcon status={message.status} />
            </span>
          )}
        </div>
      </div>
      {isOwn && message.status === "error" && (
        <button className={styles.retry} onClick={() => onRetry(message.id)}>
          Reintentar
        </button>
      )}
    </div>
  );
}
