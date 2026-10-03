// RQF-028/RQF-029 - Mentorías propias del mentee: estado y cancelación.
// navigation-service no devuelve el detalle del bloque de horario dentro de
// MentorshipOut (solo su id) — se muestra el que la propia sesión cacheó al
// solicitar (ver services/peerNameCache.ts); si la mentoría es de otra
// sesión/dispositivo, se indica que el horario no está disponible aquí.
import { useCallback, useEffect, useState } from "react";
import { CalendarClock, X } from "lucide-react";
import { cancelMentorship, listMyStudentMentorships } from "../services/navigationApi";
import { ApiError } from "../services/httpClient";
import { useAuth } from "../context/AuthContext";
import { getMentorshipSlot, getPeerName } from "../services/peerNameCache";
import type { Mentorship } from "../types";
import { PageHeader } from "../components/ui/PageHeader";
import { Banner } from "../components/ui/Banner";
import { Spinner } from "../components/ui/Spinner";
import styles from "./MyMentorshipsPage.module.css";

const STATUS_LABEL: Record<Mentorship["estado"], string> = {
  pendiente: "Pendiente de confirmación",
  confirmada: "Confirmada",
  rechazada: "Rechazada",
  cancelada: "Cancelada",
  completada: "Completada",
};

const STATUS_TONE: Record<Mentorship["estado"], string> = {
  pendiente: "pendiente",
  confirmada: "confirmada",
  rechazada: "rechazada",
  cancelada: "cancelada",
  completada: "confirmada",
};

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("es-CO", { day: "numeric", month: "short", year: "numeric" });
}

export default function MyMentorshipsPage() {
  const { accessToken } = useAuth();
  const [mentorships, setMentorships] = useState<Mentorship[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [cancellingId, setCancellingId] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!accessToken) return;
    setLoading(true);
    setError(null);
    try {
      const result = await listMyStudentMentorships(accessToken);
      setMentorships(result.sort((a, b) => b.creadaEn.localeCompare(a.creadaEn)));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No pudimos cargar tus mentorías.");
    } finally {
      setLoading(false);
    }
  }, [accessToken]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleCancel(m: Mentorship) {
    if (!accessToken) return;
    setCancellingId(m.id);
    setError(null);
    try {
      const updated = await cancelMentorship(accessToken, m.id);
      setMentorships((prev) => prev.map((x) => (x.id === updated.id ? updated : x)));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No pudimos cancelar esta mentoría.");
    } finally {
      setCancellingId(null);
    }
  }

  return (
    <div className={[styles.page, "fade-in"].join(" ")}>
      <PageHeader title="Mis mentorías" subtitle="Solicitudes enviadas y mentorías confirmadas con tus mentoras." />

      {error && <Banner tone="danger">{error}</Banner>}

      {loading ? (
        <div style={{ display: "flex", justifyContent: "center", padding: "48px 0" }}>
          <Spinner label="Cargando tus mentorías..." />
        </div>
      ) : mentorships.length === 0 ? (
        <div className={styles.emptyState}>
          <CalendarClock size={22} />
          <p>Todavía no has solicitado ninguna mentoría. Ve a "Buscar mentor" para encontrar una.</p>
        </div>
      ) : (
        <div className={styles.list}>
          {mentorships.map((m) => {
            const slot = getMentorshipSlot(m.id);
            const canCancel = m.estado === "pendiente" || m.estado === "confirmada";
            return (
              <div key={m.id} className={styles.item}>
                <div className={styles.itemInfo}>
                  <p className={styles.mentorName}>{getPeerName(m.mentorId, "Mentor")}</p>
                  {slot ? (
                    <p className={styles.slotText}>
                      {formatDate(slot.fecha)} · {slot.horaInicio.slice(0, 5)}–{slot.horaFin.slice(0, 5)}
                    </p>
                  ) : (
                    <p className={styles.slotText}>Solicitada el {formatDate(m.creadaEn)}</p>
                  )}
                </div>
                <div className={styles.itemRight}>
                  <span className={[styles.statusBadge, styles[STATUS_TONE[m.estado]]].join(" ")}>
                    {STATUS_LABEL[m.estado]}
                  </span>
                  {canCancel && (
                    <button className={styles.cancelBtn} disabled={cancellingId === m.id} onClick={() => handleCancel(m)}>
                      <X size={14} /> Cancelar
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
