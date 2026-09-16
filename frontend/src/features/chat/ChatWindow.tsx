import { useEffect, useRef, useState } from "react";
import { ArrowDown, MessageCircleOff, RadioTower, WifiOff } from "lucide-react";
import type { Conversation } from "../../types";
import { useAuth } from "../../context/AuthContext";
import { MessageBubble } from "./MessageBubble";
import { MessageInput } from "./MessageInput";
import { ConnectionBadge } from "./ConnectionBadge";
import { useChat } from "../../context/ChatContext";
import styles from "./ChatWindow.module.css";

interface ChatWindowProps {
  conversation: Conversation | null;
  onBack?: () => void;
}

function formatLastSeen(iso: string): string {
  return new Date(iso).toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit" });
}

export function ChatWindow({ conversation, onBack }: ChatWindowProps) {
  const { user } = useAuth();
  const { connectionState, sendMessage, retryMessage, loadMoreHistory, simulateDisconnect, togglePeerPresence, canSend } =
    useChat();
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const [showJumpToNew, setShowJumpToNew] = useState(false);
  const prevCount = useRef(0);

  const messages = conversation?.mensajes ?? [];

  function isNearBottom() {
    const el = scrollRef.current;
    if (!el) return true;
    return el.scrollHeight - el.scrollTop - el.clientHeight < 120;
  }

  function scrollToBottom(behavior: ScrollBehavior = "auto") {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTo({ top: el.scrollHeight, behavior });
    setShowJumpToNew(false);
  }

  // Al cambiar de conversación, ir al final.
  useEffect(() => {
    scrollToBottom("auto");
    prevCount.current = messages.length;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conversation?.id]);

  // HU017 - Escenario 2: si llega un mensaje mientras el usuario está viendo
  // mensajes antiguos, mostrar indicador en lugar de forzar el scroll.
  useEffect(() => {
    if (messages.length > prevCount.current) {
      if (isNearBottom()) {
        scrollToBottom("smooth");
      } else {
        setShowJumpToNew(true);
      }
    }
    prevCount.current = messages.length;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [messages.length]);

  function handleScroll() {
    const el = scrollRef.current;
    if (!el) return;
    if (el.scrollTop < 60) {
      loadMoreHistory();
    }
    if (isNearBottom()) setShowJumpToNew(false);
  }

  if (!conversation) {
    return (
      <div className={styles.emptyState}>
        <MessageCircleOff size={32} />
        <p>Selecciona una conversación para comenzar.</p>
      </div>
    );
  }

  const { participante } = conversation;

  return (
    <div className={styles.window}>
      <header className={styles.header}>
        {onBack && (
          <button className={styles.backBtn} onClick={onBack} aria-label="Volver">
            ←
          </button>
        )}
        <span className={styles.avatar} style={{ background: participante.avatarColor }}>
          {participante.nombre[0]}
        </span>
        <div className={styles.headerInfo}>
          <p className={styles.name}>{participante.nombre}</p>
          {/* HU019: indicador en línea / desconectada */}
          <p className={[styles.presence, participante.enLinea ? styles.presenceOnline : styles.presenceOffline].join(" ")}>
            {participante.enLinea ? "En línea" : `Desconectada · última vez ${formatLastSeen(participante.ultimaConexion)}`}
          </p>
        </div>
        <ConnectionBadge state={connectionState} />
      </header>

      <div className={styles.devToolbar}>
        <button onClick={togglePeerPresence} title="Alternar presencia del contacto (demo HU019)">
          <RadioTower size={13} /> Simular presencia
        </button>
        <button onClick={simulateDisconnect} title="Simular pérdida de conexión (demo HU019 / HU020)">
          <WifiOff size={13} /> Simular desconexión
        </button>
      </div>

      {connectionState === "reconectando" && (
        <div className={styles.reconnectBanner}>Conexión inestable: reconectando automáticamente…</div>
      )}
      {connectionState === "desconectado" && (
        <div className={styles.reconnectBannerError}>
          No se pudo restablecer la conexión. Tus próximos mensajes se enviarán al reconectar.
        </div>
      )}

      <div className={styles.messages} ref={scrollRef} onScroll={handleScroll}>
        {messages.length === 0 ? (
          <div className={styles.welcomeState}>
            <p>{conversation.mensajeBienvenida ?? "Esta es tu primera conversación. ¡Escribe el primer mensaje!"}</p>
          </div>
        ) : (
          messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} isOwn={msg.autorId === user?.id} onRetry={retryMessage} />
          ))
        )}
      </div>

      {showJumpToNew && (
        <button className={styles.jumpToNew} onClick={() => scrollToBottom("smooth")}>
          <ArrowDown size={14} /> Nuevo mensaje
        </button>
      )}

      <MessageInput
        onSend={sendMessage}
        disabled={!canSend}
        placeholder={canSend ? undefined : "Modo supervisión: el administrador no puede enviar mensajes"}
      />
    </div>
  );
}
