import type { Conversation } from "../../types";
import styles from "./ConversationList.module.css";

interface ConversationListProps {
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
}

function lastMessagePreview(conv: Conversation): string {
  const last = conv.mensajes[conv.mensajes.length - 1];
  if (!last) return conv.mensajeBienvenida ?? "Sin mensajes todavía";
  return last.texto.length > 42 ? `${last.texto.slice(0, 42)}…` : last.texto;
}

function lastMessageTime(conv: Conversation): string {
  const last = conv.mensajes[conv.mensajes.length - 1];
  if (!last) return "";
  return new Date(last.enviadoEn).toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit" });
}

export function ConversationList({ conversations, activeId, onSelect }: ConversationListProps) {
  if (conversations.length === 0) {
    return <div className={styles.empty}>Todavía no tienes conversaciones asignadas.</div>;
  }

  return (
    <ul className={styles.list}>
      {conversations.map((conv) => (
        <li key={conv.id}>
          <button
            className={[styles.item, conv.id === activeId ? styles.itemActive : ""].join(" ")}
            onClick={() => onSelect(conv.id)}
          >
            <span className={styles.avatarWrap}>
              <span className={styles.avatar} style={{ background: conv.participante.avatarColor }}>
                {conv.participante.nombre[0]}
              </span>
              <span className={[styles.dot, conv.participante.enLinea ? styles.dotOnline : styles.dotOffline].join(" ")} />
            </span>
            <span className={styles.body}>
              <span className={styles.topRow}>
                <span className={styles.name}>{conv.participante.nombre}</span>
                <span className={styles.time}>{lastMessageTime(conv)}</span>
              </span>
              <span className={styles.bottomRow}>
                <span className={styles.preview}>{lastMessagePreview(conv)}</span>
                {conv.noLeidos > 0 && <span className={styles.unread}>{conv.noLeidos}</span>}
              </span>
            </span>
          </button>
        </li>
      ))}
    </ul>
  );
}
