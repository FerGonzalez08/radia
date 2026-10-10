// Cliente HTTP del agente de orientación académica (microservicio de IA del
// repo MiguelRamos00/Proyecto-de-grado, integrado como services/agent-service,
// FastAPI, puerto 8005 en local).
//
// Contrato acordado (docs/desarrollo/integracion-radia.md de ese repo):
// - Solo POST /api/v1/conversaciones, sin JWT ni datos personales.
// - `sesion_id` es un UUID técnico generado en el navegador, nunca el id del
//   usuario. El CORS del agente solo admite la cabecera Content-Type, así que
//   aquí NO se usa httpClient (que agrega Authorization).
const API_URL = (import.meta.env.VITE_AGENTE_ORIENTACION_API_URL ?? "http://localhost:8005").replace(/\/$/, "");

export type TipoRespuestaAgente = "orientacion" | "fuera_de_alcance" | "sin_contexto_suficiente";

export interface RecursoAgente {
  titulo: string;
  descripcion: string;
  enlace: string | null;
}

export interface FuenteDocumentalAgente {
  identificador: string;
  referencia: string;
  ubicacion: string | null;
}

export interface RespuestaAgente {
  tipo_respuesta: TipoRespuestaAgente;
  respuesta: string;
  recursos: RecursoAgente[];
  fuentes_documentales: FuenteDocumentalAgente[];
  aviso_alcance: string;
  proveedor_modelo: string;
}

export class AgenteOrientacionError extends Error {
  readonly status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

function mensajeDeError(status: number, detail: unknown): string {
  if (status === 0) {
    return "No se pudo conectar con el agente de orientación. Verifica que su servicio esté encendido (agent-service, puerto 8005).";
  }
  if (status === 422) return "El mensaje no es válido. Escribe entre 1 y 1000 caracteres.";
  if (status === 404) return "No se encontró el diagnóstico asociado a esta conversación.";
  if (status === 503) {
    return typeof detail === "string" && detail
      ? `El agente no está disponible en este momento: ${detail}`
      : "El agente no está disponible en este momento. Intenta de nuevo en unos minutos.";
  }
  return "El agente no pudo responder. Intenta de nuevo.";
}

export async function enviarMensajeAgente(params: {
  sesionId: string;
  mensaje: string;
  diagnosticoId?: string;
  signal?: AbortSignal;
}): Promise<RespuestaAgente> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}/api/v1/conversaciones`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        sesion_id: params.sesionId,
        mensaje: params.mensaje,
        ...(params.diagnosticoId ? { diagnostico_id: params.diagnosticoId } : {}),
      }),
      signal: params.signal,
    });
  } catch (err) {
    if ((err as Error).name === "AbortError") throw err;
    throw new AgenteOrientacionError(mensajeDeError(0, null), 0);
  }

  if (!res.ok) {
    let detail: unknown = null;
    try {
      detail = ((await res.json()) as { detail?: unknown }).detail;
    } catch {
      /* respuesta sin cuerpo JSON */
    }
    throw new AgenteOrientacionError(mensajeDeError(res.status, detail), res.status);
  }
  return (await res.json()) as RespuestaAgente;
}

/** Comprueba GET /api/v1/salud para mostrar si el agente está en línea. */
export async function consultarSaludAgente(signal?: AbortSignal): Promise<boolean> {
  try {
    const res = await fetch(`${API_URL}/api/v1/salud`, { signal });
    return res.ok;
  } catch {
    return false;
  }
}
