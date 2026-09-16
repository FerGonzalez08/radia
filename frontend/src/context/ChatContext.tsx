import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { useAuth } from "./AuthContext";
import { MockChatSocket } from "../services/mockSocket";
import type { Conversation, SocketConnectionState } from "../types";

interface ChatContextValue {
  conversations: Conversation[];
  activeConversationId: string | null;
  setActiveConversationId: (id: string | null) => void;
  connectionState: SocketConnectionState;
  sendMessage: (texto: string) => void;
  retryMessage: (messageId: string) => void;
  loadMoreHistory: () => void;
  simulateDisconnect: () => void;
  togglePeerPresence: () => void;
  canSend: boolean;
}

const ChatContext = createContext<ChatContextValue | null>(null);

export function ChatProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const socketRef = useRef<MockChatSocket | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationIdState] = useState<string | null>(null);
  const [connectionState, setConnectionState] = useState<SocketConnectionState>("conectando");

  // Toda mutación del lado del "servidor" (mensaje nuevo, cambio de estado,
  // no leídos, presencia) se propaga a través de onConversations con un
  // snapshot fresco — es la única fuente de verdad que re-renderiza la UI.
  useEffect(() => {
    if (!user) return;
    const socket = new MockChatSocket(user.id, user.rol);
    socketRef.current = socket;
    socket.connect();

    const unsubConn = socket.onConnectionChange(setConnectionState);
    const unsubConv = socket.onConversations((convs) => {
      setConversations(convs);
      setActiveConversationIdState((prev) => prev ?? convs[0]?.id ?? null);
    });

    setConnectionState(socket.getState());
    const initial = socket.getConversations();
    setConversations(initial);
    const initialActiveId = initial[0]?.id ?? null;
    setActiveConversationIdState(initialActiveId);
    socket.setActiveConversation(initialActiveId);

    return () => {
      unsubConn();
      unsubConv();
      socket.close();
    };
  }, [user]);

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

  const simulateDisconnect = useCallback(() => {
    socketRef.current?.simulateDisconnect();
  }, []);

  const togglePeerPresence = useCallback(() => {
    if (!activeConversationId) return;
    socketRef.current?.togglePeerPresence(activeConversationId);
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
      simulateDisconnect,
      togglePeerPresence,
      canSend,
    }),
    [
      conversations,
      activeConversationId,
      setActiveConversationId,
      connectionState,
      sendMessage,
      retryMessage,
      loadMoreHistory,
      simulateDisconnect,
      togglePeerPresence,
      canSend,
    ],
  );

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}

export function useChat(): ChatContextValue {
  const ctx = useContext(ChatContext);
  if (!ctx) throw new Error("useChat debe usarse dentro de <ChatProvider>");
  return ctx;
}
