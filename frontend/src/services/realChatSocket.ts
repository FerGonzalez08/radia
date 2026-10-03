// Cliente WebSocket real de chat-service (HU016-HU022), en reemplazo de
// MockChatSocket. Misma interfaz pública (connect/close/onConnectionChange/
// onConversations/sendMessage/retryMessage/loadMoreHistory/getState/
// getConversations/setActiveConversation) para que ChatContext no cambie.
//
// Diferencia clave con el mock: chat-service abre UN canal de WebSocket por
// cada contraparte (/ws/{other_user_id}), así que aquí se mantiene un mapa
// de sockets — uno por mentoría confirmada — en vez de una sola conexión.
//
// La lista de "conversaciones" no la da chat-service: se deriva de las
// mentorías CONFIRMADAS de navigation-service (RQF-028/029), porque
// chat-service exige una mentoría activa entre ambos para abrir el canal.
// El backend tampoco expone hoy un perfil público por id para roles no
// admin, así que el nombre de la contraparte sale de peerNameCache (se llena
// al buscar mentoras o al aceptar una solicitud) con un identificador corto
// como respaldo.
import type { ChatMessage, Conversation, ConversationParticipant, Role, SocketConnectionState } from "../types";
import { buildChatWsUrl, getConversationStatus, getHistory, markAsRead } from "./chatApi";
import { listMyMentorRequests, listMyStudentMentorships } from "./navigationApi";
import { getPeerName } from "./peerNameCache";
import { pickAvatarColor } from "./api";

const MAX_RECONNECT_ATTEMPTS = 5; // RQNF 4.4 / ASR-02
const BASE_BACKOFF_MS = 800;
const ACK_TIMEOUT_MS = 10_000;

type Listener<T> = (payload: T) => void;

function conversationIdFor(a: string, b: string): string {
  return [a, b].sort().join("__");
}

function uid(): string {
  return `tmp-${Math.random().toString(36).slice(2)}${Date.now().toString(36)}`;
}

export class RealChatSocket {
  private userId: string;
  private role: Role;
  private accessToken: string;
  private closed = false;

  // Clave de todos los mapas: el id de usuario de la contraparte (no el id
  // de la conversación) — es lo que identifica el canal WS y el endpoint REST.
  private conversations = new Map<string, Conversation>();
  private sockets = new Map<string, WebSocket>();
  private reconnectAttempts = new Map<string, number>();
  private partnerStates = new Map<string, SocketConnectionState>();
  private pendingQueue = new Map<string, string[]>(); // ids temporales en orden de envío, a la espera del "ack"
  private ackTimers = new Map<string, ReturnType<typeof setTimeout>>();
  private activePartnerId: string | null = null;

  private connectionListeners: Listener<SocketConnectionState>[] = [];
  private conversationsListeners: Listener<Conversation[]>[] = [];

  constructor(userId: string, role: Role, accessToken: string) {
    this.userId = userId;
    this.role = role;
    this.accessToken = accessToken;
  }

  async connect() {
    this.closed = false;
    let partnerIds: string[] = [];
    try {
      partnerIds = await this.resolvePartnerIds();
    } catch {
      partnerIds = [];
    }
    await Promise.all(partnerIds.map((id) => this.setupConversation(id)));
    this.emitConversations();
  }

  close() {
    this.closed = true;
    for (const ws of this.sockets.values()) ws.close(1000, "client closing");
    this.sockets.clear();
    for (const timer of this.ackTimers.values()) clearTimeout(timer);
    this.ackTimers.clear();
  }

  private async resolvePartnerIds(): Promise<string[]> {
    if (this.role === "mentee") {
      const mentorships = await listMyStudentMentorships(this.accessToken);
      return Array.from(new Set(mentorships.filter((m) => m.estado === "confirmada").map((m) => m.mentorId)));
    }
    if (this.role === "mentor") {
      const mentorships = await listMyMentorRequests(this.accessToken);
      return Array.from(new Set(mentorships.filter((m) => m.estado === "confirmada").map((m) => m.estudianteId)));
    }
    // admin: chat-service no expone hoy un canal de supervisión — sin mentorías propias, sin conversaciones.
    return [];
  }

  private async setupConversation(partnerId: string) {
    const conversationId = conversationIdFor(this.userId, partnerId);
    const counterpartRole: Role = this.role === "mentor" ? "mentee" : "mentor";
    const participant: ConversationParticipant = {
      id: partnerId,
      nombre: getPeerName(partnerId, counterpartRole === "mentor" ? "Mentor" : "Estudiante"),
      rol: counterpartRole,
      enLinea: false,
      ultimaConexion: new Date().toISOString(),
      avatarColor: pickAvatarColor(partnerId),
    };

    const conversation: Conversation = { id: conversationId, participante: participant, mensajes: [], noLeidos: 0 };
    this.conversations.set(partnerId, conversation);
    this.partnerStates.set(partnerId, "conectando");

    try {
      const [history, status] = await Promise.all([
        getHistory(this.accessToken, partnerId, conversationId),
        getConversationStatus(this.accessToken, partnerId).catch(() => null),
      ]);
      conversation.mensajes = history;
      if (status) {
        conversation.participante.enLinea = status.enLinea;
        if (status.ultimaConexion) conversation.participante.ultimaConexion = status.ultimaConexion;
        conversation.noLeidos = status.noLeidos;
      }
    } catch {
      // Si falla el historial igual se intenta abrir el WS — mejor una
      // conversación vacía que bloquear todo el chat por un error puntual.
    }

    this.openSocket(partnerId);
  }

  private setPartnerState(partnerId: string, state: SocketConnectionState) {
    this.partnerStates.set(partnerId, state);
    if (partnerId === this.activePartnerId || this.activePartnerId === null) {
      this.connectionListeners.forEach((l) => l(this.getState()));
    }
  }

  private openSocket(partnerId: string) {
    if (this.closed) return;
    let ws: WebSocket;
    try {
      ws = new WebSocket(buildChatWsUrl(partnerId, this.accessToken));
    } catch {
      this.setPartnerState(partnerId, "desconectado");
      return;
    }
    this.sockets.set(partnerId, ws);

    ws.onopen = () => {
      this.reconnectAttempts.set(partnerId, 0);
      this.setPartnerState(partnerId, "conectado");
    };

    ws.onmessage = (event) => {
      this.handleIncoming(partnerId, event.data);
    };

    ws.onclose = (event) => {
      this.sockets.delete(partnerId);
      if (this.closed) return;
      // Códigos propios del backend (ver ws.py): 4401 token inválido, 4403
      // sin mentoría activa — no tiene sentido reintentar en ninguno de los dos casos.
      if (event.code === 4401 || event.code === 4403) {
        this.setPartnerState(partnerId, "desconectado");
        return;
      }
      this.setPartnerState(partnerId, "reconectando");
      this.attemptReconnect(partnerId);
    };
  }

  private attemptReconnect(partnerId: string) {
    const attempts = this.reconnectAttempts.get(partnerId) ?? 0;
    if (attempts >= MAX_RECONNECT_ATTEMPTS) {
      this.setPartnerState(partnerId, "desconectado");
      return;
    }
    const delayMs = BASE_BACKOFF_MS * Math.pow(2, attempts);
    this.reconnectAttempts.set(partnerId, attempts + 1);
    setTimeout(() => {
      if (this.closed) return;
      this.openSocket(partnerId);
    }, delayMs);
  }

  private handleIncoming(partnerId: string, raw: string) {
    const conversation = this.conversations.get(partnerId);
    if (!conversation) return;
    let data: Record<string, unknown>;
    try {
      data = JSON.parse(raw);
    } catch {
      return;
    }

    if (data.type === "message") {
      const incoming: ChatMessage = {
        id: String(data.id),
        conversationId: conversation.id,
        autorId: String(data.sender_user_id),
        texto: String(data.content ?? ""),
        enviadoEn: String(data.created_at ?? new Date().toISOString()),
        status: "entregado",
      };
      conversation.mensajes.push(incoming);
      if (this.activePartnerId !== partnerId) conversation.noLeidos += 1;
      this.emitConversations();
      return;
    }

    if (data.type === "ack") {
      const queue = this.pendingQueue.get(partnerId) ?? [];
      const tempId = queue.shift();
      this.pendingQueue.set(partnerId, queue);
      if (tempId) {
        const timer = this.ackTimers.get(tempId);
        if (timer) {
          clearTimeout(timer);
          this.ackTimers.delete(tempId);
        }
        const msg = conversation.mensajes.find((m) => m.id === tempId);
        if (msg) {
          msg.id = String(data.id);
          msg.status = data.status === "entregado" ? "entregado" : "enviado";
        }
      }
      this.emitConversations();
      return;
    }

    if (data.type === "presence") {
      conversation.participante.enLinea = Boolean(data.online);
      if (typeof data.last_seen_at === "string") conversation.participante.ultimaConexion = data.last_seen_at;
      this.emitConversations();
    }
  }

  getState(): SocketConnectionState {
    if (this.activePartnerId) return this.partnerStates.get(this.activePartnerId) ?? "conectando";
    // Sin conversación activa: "conectado" si ya se resolvió el arranque
    // (aunque no haya ninguna mentoría, no tiene sentido mostrar "conectando" para siempre).
    return this.conversations.size === 0 ? "conectado" : (this.partnerStates.get(this.activePartnerId!) ?? "conectado");
  }

  getConversations(): Conversation[] {
    return Array.from(this.conversations.values());
  }

  setActiveConversation(conversationId: string | null) {
    const entry = Array.from(this.conversations.entries()).find(([, c]) => c.id === conversationId);
    this.activePartnerId = entry ? entry[0] : null;
    if (entry) {
      const [partnerId, conversation] = entry;
      if (conversation.noLeidos > 0) {
        conversation.noLeidos = 0;
        this.emitConversations();
      }
      markAsRead(this.accessToken, partnerId).catch(() => undefined);
    }
    this.connectionListeners.forEach((l) => l(this.getState()));
  }

  emitConversations() {
    this.conversationsListeners.forEach((l) => l(this.getConversations()));
  }

  sendMessage(conversationId: string, texto: string) {
    const entry = Array.from(this.conversations.entries()).find(([, c]) => c.id === conversationId);
    if (!entry) return;
    const [partnerId, conversation] = entry;
    this.pushOptimistic(partnerId, conversation, texto);
  }

  private pushOptimistic(partnerId: string, conversation: Conversation, texto: string) {
    const tempId = uid();
    const ws = this.sockets.get(partnerId);
    const isOpen = ws?.readyState === WebSocket.OPEN;

    const optimistic: ChatMessage = {
      id: tempId,
      conversationId: conversation.id,
      autorId: this.userId,
      texto,
      enviadoEn: new Date().toISOString(),
      status: isOpen ? "enviado" : "pendiente",
    };
    conversation.mensajes.push(optimistic);
    this.emitConversations();

    if (!isOpen) return; // queda "pendiente"; el usuario puede reintentar con el botón (retryMessage).

    this.sendOverSocket(partnerId, tempId, texto);
  }

  private sendOverSocket(partnerId: string, tempId: string, texto: string) {
    const ws = this.sockets.get(partnerId);
    if (!ws || ws.readyState !== WebSocket.OPEN) return;

    const queue = this.pendingQueue.get(partnerId) ?? [];
    queue.push(tempId);
    this.pendingQueue.set(partnerId, queue);

    ws.send(JSON.stringify({ content: texto }));

    const timer = setTimeout(() => {
      const conversation = this.conversations.get(partnerId);
      const msg = conversation?.mensajes.find((m) => m.id === tempId);
      if (msg && msg.status !== "entregado" && msg.status !== "enviado") return;
      if (msg && msg.id === tempId) {
        // Nunca llegó el "ack" (p. ej. la conexión se cayó justo después de
        // enviar) — se marca error para que la persona pueda reintentar.
        msg.status = "error";
        this.emitConversations();
      }
    }, ACK_TIMEOUT_MS);
    this.ackTimers.set(tempId, timer);
  }

  retryMessage(conversationId: string, messageId: string) {
    const entry = Array.from(this.conversations.entries()).find(([, c]) => c.id === conversationId);
    if (!entry) return;
    const [partnerId, conversation] = entry;
    const msg = conversation.mensajes.find((m) => m.id === messageId);
    if (!msg) return;
    msg.status = "pendiente";
    this.emitConversations();
    this.sendOverSocket(partnerId, messageId, msg.texto);
    if (this.sockets.get(partnerId)?.readyState === WebSocket.OPEN) {
      msg.status = "enviado";
      this.emitConversations();
    }
  }

  /** RQF-021 - Historial paginado: pide mensajes anteriores al más antiguo cargado. */
  async loadMoreHistory(conversationId: string) {
    const entry = Array.from(this.conversations.entries()).find(([, c]) => c.id === conversationId);
    if (!entry) return;
    const [partnerId, conversation] = entry;
    const oldest = conversation.mensajes[0];
    if (!oldest || oldest.id.startsWith("tmp-")) return;
    try {
      const older = await getHistory(this.accessToken, partnerId, conversation.id, oldest.enviadoEn);
      if (older.length === 0) return;
      conversation.mensajes = [...older, ...conversation.mensajes];
      this.emitConversations();
    } catch {
      // fallo silencioso — el usuario puede reintentar haciendo scroll de nuevo.
    }
  }

  onConnectionChange(cb: Listener<SocketConnectionState>) {
    this.connectionListeners.push(cb);
    return () => {
      this.connectionListeners = this.connectionListeners.filter((l) => l !== cb);
    };
  }

  onConversations(cb: Listener<Conversation[]>) {
    this.conversationsListeners.push(cb);
    return () => {
      this.conversationsListeners = this.conversationsListeners.filter((l) => l !== cb);
    };
  }
}
