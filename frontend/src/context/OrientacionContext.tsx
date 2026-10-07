// Estado compartido del chat con el agente de orientación (IA).
// Lo usan tanto la burbuja flotante como la página /app/orientacion, así la
// conversación no se pierde al pasar de una a otra. No se persiste nada: al
// cerrar la pestaña o la sesión se descarta (el agente tampoco guarda la
// conversación; ver integracion-radia.md del repo del agente).
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import {
  AgenteOrientacionError,
  consultarSaludAgente,
  enviarMensajeAgente,
  type RespuestaAgente,
} from "../services/agenteOrientacionApi";

export type MensajeOrientacion =
  | { id: string; autor: "usuario"; texto: string; enviadoEn: string }
  | { id: string; autor: "agente"; respuesta: RespuestaAgente; enviadoEn: string };

export type EstadoAgente = "verificando" | "disponible" | "no_disponible";

interface OrientacionContextValue {
  mensajes: MensajeOrientacion[];
  enviando: boolean;
  error: string | null;
  estadoAgente: EstadoAgente;
  enviar: (texto: string) => Promise<void>;
  reiniciar: () => void;
  reintentarConexion: () => void;
}

const OrientacionContext = createContext<OrientacionContextValue | null>(null);

function nuevoId(): string {
  return crypto.randomUUID();
}

export function OrientacionProvider({ children }: { children: ReactNode }) {
  // UUID técnico de la conversación — nunca el id, correo ni JWT del usuario.
  const sesionIdRef = useRef<string>(nuevoId());
  const [mensajes, setMensajes] = useState<MensajeOrientacion[]>([]);
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [estadoAgente, setEstadoAgente] = useState<EstadoAgente>("verificando");
  const [pingTick, setPingTick] = useState(0);

  useEffect(() => {
    const ctrl = new AbortController();
    consultarSaludAgente(ctrl.signal).then((ok) => {
      if (!ctrl.signal.aborted) setEstadoAgente(ok ? "disponible" : "no_disponible");
    });
    return () => ctrl.abort();
  }, [pingTick]);

  const enviar = useCallback(
    async (texto: string) => {
      const limpio = texto.trim();
      if (!limpio || enviando) return;
      if (limpio.length > 1000) {
        setError("El mensaje no puede superar los 1000 caracteres.");
        return;
      }
      setError(null);
      setMensajes((prev) => [...prev, { id: nuevoId(), autor: "usuario", texto: limpio, enviadoEn: new Date().toISOString() }]);
      setEnviando(true);
      try {
        const respuesta = await enviarMensajeAgente({ sesionId: sesionIdRef.current, mensaje: limpio });
        setMensajes((prev) => [...prev, { id: nuevoId(), autor: "agente", respuesta, enviadoEn: new Date().toISOString() }]);
        setEstadoAgente("disponible");
      } catch (err) {
        const status = err instanceof AgenteOrientacionError ? err.status : -1;
        setError(err instanceof Error ? err.message : "El agente no pudo responder.");
        if (status === 0) setEstadoAgente("no_disponible");
      } finally {
        setEnviando(false);
      }
    },
    [enviando],
  );

  const reiniciar = useCallback(() => {
    sesionIdRef.current = nuevoId();
    setMensajes([]);
    setError(null);
  }, []);

  const reintentarConexion = useCallback(() => {
    setEstadoAgente("verificando");
    setPingTick((t) => t + 1);
  }, []);

  const value = useMemo(
    () => ({ mensajes, enviando, error, estadoAgente, enviar, reiniciar, reintentarConexion }),
    [mensajes, enviando, error, estadoAgente, enviar, reiniciar, reintentarConexion],
  );

  return <OrientacionContext.Provider value={value}>{children}</OrientacionContext.Provider>;
}

export function useOrientacion(): OrientacionContextValue {
  const ctx = useContext(OrientacionContext);
  if (!ctx) throw new Error("useOrientacion debe usarse dentro de <OrientacionProvider>");
  return ctx;
}
