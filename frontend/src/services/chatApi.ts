// Cliente REST de chat-service (FastAPI, puerto 8004 en local — ver
// docker-compose.yml del repo de backend). El envío/recepción de mensajes
// en vivo va por WebSocket (ver realChatSocket.ts); este módulo cubre
// historial paginado, marcar como leído y el estado de una conversación.
import type { ChatMessage, MessageStatus } from "../types";
import { createApiClient } from "./httpClient";

const API_URL = (import.meta.env.VITE_CHAT_API_URL ?? "http://localhost:8004").replace(/\/$/, "");
const { request, authHeaders, API_BASE } = createApiClient(API_URL);

interface MessageOut {
  id: string;
  conversation_id: string;
  sender_user_id: string;
  content: string;
  status: string;
  created_at: string;
  read_at: string | null;
}

interface ConversationStatusOut {
  conversation_id: string;
  online: boolean;
  last_seen_at: string | null;
  unread_count: number;
}

function mapMessage(m: MessageOut, conversationId: string): ChatMessage {
  return {
    id: m.id,
    conversationId,
    autorId: m.sender_user_id,
    texto: m.content,
    enviadoEn: m.created_at,
    status: (m.status as MessageStatus) ?? "enviado",
  };
}

/** RQF-021 - Historial paginado ("before" = cursor hacia atrás en el tiempo). */
export async function getHistory(
  accessToken: string,
  otherUserId: string,
  conversationId: string,
  before?: string,
  limit = 50,
): Promise<ChatMessage[]> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (before) params.set("before", before);
  const result = await request<MessageOut[]>(`/conversations/${otherUserId}/messages?${params.toString()}`, {
    headers: authHeaders(accessToken),
  });
  return result.map((m) => mapMessage(m, conversationId));
}

export async function markAsRead(accessToken: string, otherUserId: string): Promise<void> {
  await request<void>(`/conversations/${otherUserId}/read`, { method: "POST", headers: authHeaders(accessToken) });
}

export async function getConversationStatus(
  accessToken: string,
  otherUserId: string,
): Promise<{ enLinea: boolean; ultimaConexion: string | null; noLeidos: number }> {
  const result = await request<ConversationStatusOut>(`/conversations/${otherUserId}/status`, {
    headers: authHeaders(accessToken),
  });
  return { enLinea: result.online, ultimaConexion: result.last_seen_at, noLeidos: result.unread_count };
}

/** El endpoint WS vive en la misma base que el resto de chat-service, solo cambia el esquema (http -> ws). */
export function buildChatWsUrl(otherUserId: string, accessToken: string): string {
  const wsBase = API_BASE.replace(/^http/, "ws");
  return `${wsBase}/ws/${otherUserId}?token=${encodeURIComponent(accessToken)}`;
}
