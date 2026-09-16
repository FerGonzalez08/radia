// Simulación de un servicio de chat en tiempo real por WebSocket (HU016-022).
// La forma de la API (connect/on.../send/close) es la misma que tendría un
// cliente real hablando con el microservicio de chat (Node.js + ws) descrito
// en el ASR-01 / ASR-02 del proyecto (p95 <= 1.5s de entrega, reconexión con
// backoff progresivo <= 5 reintentos). Sustituir esta clase por un cliente
// WebSocket real no debería requerir cambios en ChatContext ni en la UI.
import type { ChatMessage, Conversation, ConversationParticipant, MessageStatus, Role, SocketConnectionState } from "../types";

const STORE_PREFIX = "radia.chat.";
const MAX_RECONNECT_ATTEMPTS = 5; // RQNF 4.4 / ASR-02
const BASE_BACKOFF_MS = 800;

type Listener<T> = (payload: T) => void;

interface SeedContact {
  id: string;
  nombre: string;
  rol: Role;
  avatarColor: string;
  mensajeBienvenida: string;
  guion: string[]; // respuestas automáticas del "bot" mentor/mentee para simular tiempo real
}

const CONTACTS_BY_ROLE: Record<Role, SeedContact[]> = {
  mentee: [
    {
      id: "u-mentor",
      nombre: "Laura Gómez",
      rol: "mentor",
      avatarColor: "#9A2177",
      mensajeBienvenida: "Aún no tienen mensajes. ¡Envía el primero para romper el hielo!",
      guion: [
        "¡Hola! Qué bueno verte por aquí 🙂",
        "Cuéntame, ¿en qué semestre vas y qué te gustaría reforzar primero?",
        "Perfecto, armemos un plan corto para las próximas semanas.",
        "Cuando quieras agendamos una llamada para revisar tu portafolio.",
      ],
    },
  ],
  mentor: [
    {
      id: "u-mentee",
      nombre: "Valentina Ríos",
      rol: "mentee",
      avatarColor: "#D1155B",
      mensajeBienvenida: "Aún no tienen mensajes con esta mentee.",
      guion: [
        "¡Hola! Gracias por aceptar acompañarme 🙌",
        "Estoy en 7º semestre de Ing. de Sistemas, me interesa backend y cloud.",
        "Genial, me encantaría revisar mi hoja de vida contigo.",
      ],
    },
    {
      id: "u-mentee-2",
      nombre: "Daniela Suárez",
      rol: "mentee",
      avatarColor: "#682D90",
      mensajeBienvenida: "Aún no tienen mensajes con esta mentee.",
      guion: ["Hola, ¡mucho gusto! Estoy arrancando en desarrollo web.", "¿Podrías recomendarme por dónde empezar?"],
    },
  ],
  admin: [
    {
      id: "u-mentor",
      nombre: "Laura Gómez",
      rol: "mentor",
      avatarColor: "#9A2177",
      mensajeBienvenida: "Vista de supervisión: como administrador puedes consultar, no enviar mensajes.",
      guion: [],
    },
  ],
};

function loadMessages(conversationId: string): ChatMessage[] {
  try {
    const raw = localStorage.getItem(STORE_PREFIX + conversationId);
    return raw ? (JSON.parse(raw) as ChatMessage[]) : [];
  } catch {
    return [];
  }
}

function saveMessages(conversationId: string, messages: ChatMessage[]) {
  localStorage.setItem(STORE_PREFIX + conversationId, JSON.stringify(messages));
}

function uid(): string {
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

export class MockChatSocket {
  private currentUserId: string;
  private currentUserRole: Role;
  private conversations: Map<string, Conversation> = new Map();
  private activeConversationId: string | null = null;
  private state: SocketConnectionState = "conectando";
  private reconnectAttempts = 0;

  private messageListeners: Listener<{ conversationId: string; message: ChatMessage }>[] = [];
  private connectionListeners: Listener<SocketConnectionState>[] = [];
  private presenceListeners: Listener<{ conversationId: string; enLinea: boolean; ultimaConexion: string }>[] = [];
  private conversationsListeners: Listener<Conversation[]>[] = [];
  private unreadListeners: Listener<{ conversationId: string; noLeidos: number }>[] = [];

  constructor(userId: string, role: Role) {
    this.currentUserId = userId;
    this.currentUserRole = role;
    this.seedConversations();
  }

  private seedConversations() {
    const contacts = CONTACTS_BY_ROLE[this.currentUserRole] ?? [];
    for (const contact of contacts) {
      const conversationId = [this.currentUserId, contact.id].sort().join("__");
      const participant: ConversationParticipant = {
        id: contact.id,
        nombre: contact.nombre,
        rol: contact.rol,
        enLinea: true,
        ultimaConexion: new Date().toISOString(),
        avatarColor: contact.avatarColor,
      };
      this.conversations.set(conversationId, {
        id: conversationId,
        participante: participant,
        mensajes: loadMessages(conversationId).slice(-50),
        noLeidos: 0,
        mensajeBienvenida: contact.mensajeBienvenida,
      });
    }
  }

  private scriptFor(participantId: string): string[] {
    for (const list of Object.values(CONTACTS_BY_ROLE)) {
      const found = list.find((c) => c.id === participantId);
      if (found) return found.guion;
    }
    return [];
  }

  // --- ciclo de vida de la conexión -----------------------------------
  connect() {
    this.setState("conectando");
    setTimeout(() => {
      this.setState("conectado");
      this.reconnectAttempts = 0;
      this.emitConversations();
    }, 500);
  }

  close() {
    this.setState("desconectado");
  }

  /** Botón de demo para HU019/HU020/HU022: simula pérdida de conexión. */
  simulateDisconnect() {
    if (this.state === "desconectado" || this.state === "reconectando") return;
    this.setState("reconectando");
    this.attemptReconnect();
  }

  private attemptReconnect() {
    if (this.reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
      this.setState("desconectado");
      return;
    }
    const delayMs = BASE_BACKOFF_MS * Math.pow(2, this.reconnectAttempts); // backoff progresivo
    this.reconnectAttempts += 1;
    setTimeout(() => {
      const succeeds = this.reconnectAttempts >= 1; // en la demo, el 1er intento ya reconecta
      if (succeeds) {
        this.setState("conectado");
        this.reconnectAttempts = 0;
        this.flushPendingMessages();
      } else {
        this.attemptReconnect();
      }
    }, delayMs);
  }

  private setState(next: SocketConnectionState) {
    this.state = next;
    this.connectionListeners.forEach((l) => l(next));
  }

  getState() {
    return this.state;
  }

  /** Botón de demo para HU019: alterna el estado en línea/desconectada del contacto. */
  togglePeerPresence(conversationId: string) {
    const conv = this.conversations.get(conversationId);
    if (!conv) return;
    conv.participante.enLinea = !conv.participante.enLinea;
    conv.participante.ultimaConexion = new Date().toISOString();
    this.presenceListeners.forEach((l) =>
      l({ conversationId, enLinea: conv.participante.enLinea, ultimaConexion: conv.participante.ultimaConexion }),
    );
    this.emitConversations();
  }

  // --- conversaciones ----------------------------------------------------
  getConversations(): Conversation[] {
    return Array.from(this.conversations.values());
  }

  setActiveConversation(conversationId: string | null) {
    this.activeConversationId = conversationId;
    if (conversationId) {
      const conv = this.conversations.get(conversationId);
      if (conv && conv.noLeidos > 0) {
        conv.noLeidos = 0;
        this.unreadListeners.forEach((l) => l({ conversationId, noLeidos: 0 }));
        this.emitConversations();
      }
    }
  }

  emitConversations() {
    this.conversationsListeners.forEach((l) => l(this.getConversations()));
  }

  // --- mensajería ----------------------------------------------------
  /** HU018: historial paginado, últimos 50 y "cargar más" hacia atrás. */
  loadMoreHistory(conversationId: string) {
    const conv = this.conversations.get(conversationId);
    if (!conv) return;
    const all = loadMessages(conversationId);
    const remaining = all.length - conv.mensajes.length;
    if (remaining <= 0) return;
    const start = Math.max(0, remaining - 20);
    const older = all.slice(start, remaining);
    if (older.length === 0) return;
    conv.mensajes.unshift(...older);
    this.emitConversations();
  }

  sendMessage(conversationId: string, texto: string): ChatMessage {
    const conv = this.conversations.get(conversationId);
    if (!conv) throw new Error("Conversación no encontrada");

    const optimistic: ChatMessage = {
      id: uid(),
      conversationId,
      autorId: this.currentUserId,
      texto,
      enviadoEn: new Date().toISOString(),
      status: this.state === "conectado" ? "enviado" : "pendiente",
    };

    conv.mensajes.push(optimistic);
    saveMessages(conversationId, loadMessages(conversationId).concat(optimistic));
    this.messageListeners.forEach((l) => l({ conversationId, message: optimistic }));
    this.emitConversations();

    if (this.state === "conectado") {
      this.deliverToServer(conversationId, optimistic);
    }
    // Si no hay conexión, el mensaje queda "pendiente" y se reintenta al
    // recuperar la conexión (ver flushPendingMessages / HU016 - Escenario 3).

    return optimistic;
  }

  private deliverToServer(conversationId: string, message: ChatMessage) {
    const latencyMs = 500 + Math.random() * 700; // ~ p95 simulado del ASR-01
    setTimeout(() => {
      // HU022 - Escenario 2: pequeña probabilidad de fallo de entrega.
      const fails = Math.random() < 0.08;
      this.updateMessageStatus(conversationId, message.id, fails ? "error" : "entregado");
      if (!fails) this.maybeAutoReply(conversationId);
    }, latencyMs);
  }

  retryMessage(conversationId: string, messageId: string) {
    const conv = this.conversations.get(conversationId);
    const msg = conv?.mensajes.find((m) => m.id === messageId);
    if (!msg) return;
    this.updateMessageStatus(conversationId, messageId, "enviado");
    this.deliverToServer(conversationId, msg);
  }

  private flushPendingMessages() {
    for (const [conversationId, conv] of this.conversations) {
      const pending = conv.mensajes.filter((m) => m.status === "pendiente");
      for (const msg of pending) {
        this.updateMessageStatus(conversationId, msg.id, "enviado");
        this.deliverToServer(conversationId, msg);
      }
    }
  }

  private updateMessageStatus(conversationId: string, messageId: string, status: MessageStatus) {
    const conv = this.conversations.get(conversationId);
    if (!conv) return;
    const msg = conv.mensajes.find((m) => m.id === messageId);
    if (!msg) return;
    msg.status = status;
    const stored = loadMessages(conversationId).map((m) => (m.id === messageId ? { ...m, status } : m));
    saveMessages(conversationId, stored);
    this.messageListeners.forEach((l) => l({ conversationId, message: msg }));
    this.emitConversations();
  }

  /** HU017: simula la recepción en tiempo real de un mensaje entrante. */
  private maybeAutoReply(conversationId: string) {
    const conv = this.conversations.get(conversationId);
    if (!conv) return;
    const script = this.scriptFor(conv.participante.id);
    if (script.length === 0) return;

    const sentByOther = conv.mensajes.filter((m) => m.autorId === conv.participante.id).length;
    const reply = script[Math.min(sentByOther, script.length - 1)];
    if (!reply) return;

    setTimeout(() => {
      const incoming: ChatMessage = {
        id: uid(),
        conversationId,
        autorId: conv.participante.id,
        texto: reply,
        enviadoEn: new Date().toISOString(),
        status: "entregado",
      };
      conv.mensajes.push(incoming);
      saveMessages(conversationId, loadMessages(conversationId).concat(incoming));
      this.messageListeners.forEach((l) => l({ conversationId, message: incoming }));

      if (this.activeConversationId !== conversationId) {
        conv.noLeidos += 1;
        this.unreadListeners.forEach((l) => l({ conversationId, noLeidos: conv.noLeidos }));
      }
      this.emitConversations();
    }, 1400 + Math.random() * 1600);
  }

  // --- suscripciones ----------------------------------------------------
  onMessage(cb: Listener<{ conversationId: string; message: ChatMessage }>) {
    this.messageListeners.push(cb);
    return () => {
      this.messageListeners = this.messageListeners.filter((l) => l !== cb);
    };
  }

  onConnectionChange(cb: Listener<SocketConnectionState>) {
    this.connectionListeners.push(cb);
    return () => {
      this.connectionListeners = this.connectionListeners.filter((l) => l !== cb);
    };
  }

  onUnreadChange(cb: Listener<{ conversationId: string; noLeidos: number }>) {
    this.unreadListeners.push(cb);
    return () => {
      this.unreadListeners = this.unreadListeners.filter((l) => l !== cb);
    };
  }

  onConversations(cb: Listener<Conversation[]>) {
    this.conversationsListeners.push(cb);
    return () => {
      this.conversationsListeners = this.conversationsListeners.filter((l) => l !== cb);
    };
  }

  onPresenceChange(cb: Listener<{ conversationId: string; enLinea: boolean; ultimaConexion: string }>) {
    this.presenceListeners.push(cb);
    return () => {
      this.presenceListeners = this.presenceListeners.filter((l) => l !== cb);
    };
  }
}
