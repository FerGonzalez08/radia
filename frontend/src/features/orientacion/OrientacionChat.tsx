// Interfaz del chat con el agente de orientación académica (IA).
// Se diferencia a propósito del chat de mentorías: no usa WebSocket, no hay
// otra persona del otro lado y siempre muestra el aviso de alcance del agente.
import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import { Bot, ExternalLink, FileText, RefreshCw, RotateCcw, Send, Sparkles } from "lucide-react";
import { useOrientacion, type MensajeOrientacion } from "../../context/OrientacionContext";
import styles from "./OrientacionChat.module.css";

const SUGERENCIAS = [
  "Quiero fortalecer mis conocimientos de bases de datos",
  "¿Cómo puedo mejorar mi trabajo en equipo en proyectos de software?",
  "¿Por dónde empiezo a aprender programación orientada a objetos?",
];

const ETIQUETA_TIPO: Record<string, string> = {
  orientacion: "Orientación",
  fuera_de_alcance: "Fuera de alcance",
  sin_contexto_suficiente: "Necesito más contexto",
};

function hora(iso: string): string {
  return new Date(iso).toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit" });
}

function MensajeAgente({ m, compact }: { m: Extract<MensajeOrientacion, { autor: "agente" }>; compact: boolean }) {
  const r = m.respuesta;
  return (
    <div className={[styles.msg, styles.msgAgente].join(" ")}>
      <span className={[styles.tipo, styles[`tipo_${r.tipo_respuesta}`] ?? ""].join(" ")}>
        {ETIQUETA_TIPO[r.tipo_respuesta] ?? r.tipo_respuesta}
      </span>
      <p className={styles.texto}>{r.respuesta}</p>

      {r.recursos.length > 0 && (
        <div className={styles.bloque}>
          <p className={styles.bloqueTitulo}>Recursos sugeridos</p>
          <ul className={styles.recursos}>
            {r.recursos.map((rec) => (
              <li key={rec.titulo}>
                {rec.enlace ? (
                  <a href={rec.enlace} target="_blank" rel="noreferrer">
                    {rec.titulo} <ExternalLink size={12} aria-hidden />
                  </a>
                ) : (
                  <strong>{rec.titulo}</strong>
                )}
                {!compact && <span>{rec.descripcion}</span>}
              </li>
            ))}
          </ul>
        </div>
      )}

      {r.fuentes_documentales.length > 0 && (
        <div className={styles.bloque}>
          <p className={styles.bloqueTitulo}>Fuentes consultadas</p>
          <ul className={styles.fuentes}>
            {r.fuentes_documentales.map((f) => (
              <li key={f.identificador}>
                <FileText size={12} aria-hidden /> {f.referencia}
                {f.ubicacion ? ` · ${f.ubicacion}` : ""}
              </li>
            ))}
          </ul>
        </div>
      )}

      <p className={styles.aviso}>{r.aviso_alcance}</p>
      <span className={styles.meta}>{hora(m.enviadoEn)}</span>
    </div>
  );
}

export function OrientacionChat({ compact = false }: { compact?: boolean }) {
  const { mensajes, enviando, error, estadoAgente, enviar, reiniciar, reintentarConexion } = useOrientacion();
  const [texto, setTexto] = useState("");
  const listaRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    listaRef.current?.scrollTo({ top: listaRef.current.scrollHeight, behavior: "smooth" });
  }, [mensajes.length, enviando]);

  async function onSubmit(e?: FormEvent) {
    e?.preventDefault();
    const t = texto;
    if (!t.trim()) return;
    setTexto("");
    await enviar(t);
  }

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void onSubmit();
    }
  }

  return (
    <div className={[styles.chat, compact ? styles.compact : ""].join(" ")}>
      <div className={styles.estado}>
        <span className={[styles.punto, styles[`punto_${estadoAgente}`]].join(" ")} aria-hidden />
        <span>
          {estadoAgente === "disponible" && "Agente en línea"}
          {estadoAgente === "verificando" && "Conectando con el agente…"}
          {estadoAgente === "no_disponible" && "Agente sin conexión"}
        </span>
        {estadoAgente === "no_disponible" && (
          <button type="button" className={styles.linkBtn} onClick={reintentarConexion}>
            <RefreshCw size={12} /> Reintentar
          </button>
        )}
        {mensajes.length > 0 && (
          <button type="button" className={styles.linkBtn} onClick={reiniciar} title="Empezar una conversación nueva">
            <RotateCcw size={12} /> Nueva
          </button>
        )}
      </div>

      <div className={styles.lista} ref={listaRef} aria-live="polite">
        {mensajes.length === 0 ? (
          <div className={styles.vacio}>
            <span className={styles.vacioIcono}>
              <Sparkles size={22} />
            </span>
            <p className={styles.vacioTitulo}>¿En qué quieres fortalecerte?</p>
            <p className={styles.vacioTexto}>
              Cuéntame qué competencia técnica o actitudinal quieres trabajar y te doy una orientación inicial con
              recursos.
            </p>
            <div className={styles.sugerencias}>
              {SUGERENCIAS.slice(0, compact ? 2 : 3).map((s) => (
                <button key={s} type="button" className={styles.sugerencia} onClick={() => void enviar(s)} disabled={enviando}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          mensajes.map((m) =>
            m.autor === "usuario" ? (
              <div key={m.id} className={[styles.msg, styles.msgUsuario].join(" ")}>
                <p className={styles.texto}>{m.texto}</p>
                <span className={styles.meta}>{hora(m.enviadoEn)}</span>
              </div>
            ) : (
              <MensajeAgente key={m.id} m={m} compact={compact} />
            ),
          )
        )}
        {enviando && (
          <div className={[styles.msg, styles.msgAgente, styles.escribiendo].join(" ")}>
            <Bot size={14} /> <span>El agente está pensando</span>
            <span className={styles.dots} aria-hidden>
              <i />
              <i />
              <i />
            </span>
          </div>
        )}
      </div>

      {error && (
        <p className={styles.error} role="alert">
          {error}
        </p>
      )}

      <form className={styles.form} onSubmit={onSubmit}>
        <textarea
          className={styles.input}
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Escribe tu pregunta…"
          rows={compact ? 1 : 2}
          maxLength={1000}
          disabled={enviando}
          aria-label="Mensaje para el agente de orientación"
        />
        <button type="submit" className={styles.send} disabled={enviando || !texto.trim()} aria-label="Enviar mensaje">
          <Send size={16} />
        </button>
      </form>
      <p className={styles.pie}>
        Orientación general de aprendizaje, no es una evaluación académica, psicológica ni profesional. Tu mensaje no
        se comparte con otras personas.
      </p>
    </div>
  );
}
