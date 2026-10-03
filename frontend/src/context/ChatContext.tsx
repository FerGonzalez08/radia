import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { useAuth } from "./AuthContext";
import { RealChatSocket } from "../services/realChatSocket";
import type { Conversation, SocketConnectionState } from "../types";

interface ChatContextValue {
  conversations: Conversation[];
  activeConversationId: string | null;
  setActiveConversationId: (id: string | null) => void;
  connectionState: SocketConnectionState;
  sendMessage: (texto: string) => void;
  retryMessage: (messageId: string) => void;
  loadMoreHistory: () => void;
  canSend: boolean;
}

const ChatContext = createContext<ChatContextValue | null>(null);

export function ChatProvider({ children }: { children: ReactNode }) {
  const { user, accessToken } = useAuth();
  const socketRef = useRef<RealChatSocket | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationIdState] = useState<string | null>(null);
  const [connectionState, setConnectionState] = useState<SocketConnectionState>("conectando");

  // Toda mutación (mensaje nuevo, presencia, no leídos) se propaga a través
  // de onConversations con un snapshot fresco — es la única fuente de
  // verdad que re-renderiza la UI. La conexión real a chat-service abre un
  // canal WebSocket por cada mentoría confirmada (ver realChatSocket.ts).
  useEffect(() => {
    if (!user || !accessToken) return;
    const socket = new RealChatSocket(user.id, user.rol, accessToken);
    socketRef.current = socket;

    const unsubConn = socket.onConnectionChange(setConnectionState);
    const unsubConv = socket.onConversations((convs) => {
      setConversations(convs);
      setActiveConversationIdState((prev) => prev ?? convs[0]?.id ?? null);
    });

    socket.connect().then(() => {
      const initial = socket.getConversations();
      setConversations(initial);
      setConnectionState(socket.getState());
      const initialActiveId = initial[0]?.id ?? null;
      setActiveConversationIdState(initialActiveId);
      socket.setActiveConversation(initialActiveId);
    });

    return () => {
      unsubConn();
      unsubConv();
      socket.close();
    };
  }, [user, accessToken]);

  const setActiveConversationId = useCallback((id: string | null) => {
    socketRef.current?.setActiveConversation(id);
    setActiveConversationIdState(id);
  }, []);

  const sendMessage = useCallback(
    (texto: string) => {
      if (!activeConversationId || !texto.trim()) return;
      socketRef.current?.sendMessage(activeConversationId, texto.trim());
    },
    [activeConversationId],
  );

  const retryMessage = useCallback(
    (messageId: string) => {
      if (!activeConversationId) return;
      socketRef.current?.retryMessage(activeConversationId, messageId);
    },
    [activeConversationId],
  );

  const loadMoreHistory = useCallback(() => {
    if (!activeConversationId) return;
    socketRef.current?.loadMoreHistory(activeConversationId);
  }, [activeConversationId]);

  // Admin: rol de supervisión, no puede enviar mensajes (ver matriz de permisos).
  const canSend = user?.rol !== "admin";

  const value = useMemo<ChatContextValue>(
    () => ({
      conversations,
      activeConversationId,
      setActiveConversationId,
      connectionState,
      sendMessage,
      retryMessage,
      loadMoreHistory,
      canSend,
    }),
    [conversations, activeConversationId, setActiveConversationId, connectionState, sendMessage, retryMessage, loadMoreHistory, canSend],
  );

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}

export function useChat(): ChatContextValue {
  const ctx = useContext(ChatContext);
  if (!ctx) throw new Error("useChat debe usarse dentro de <ChatProvider>");
  return ctx;
}
