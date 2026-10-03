// RQF-029 - Solicitudes de mentoría recibidas: aceptar/rechazar pendientes
// y ver el historial. navigation-service no incluye el detalle del bloque
// dentro de MentorshipOut, pero la mentora sí puede leer TODOS sus propios
// bloques (libres y reservados) vía GET /mentors/me/availability, así que
// cruzamos por availability_slot_id para mostrar fecha/hora reales.
import { useCallback, useEffect, useState } from "react";
import { CalendarClock, Check, Inbox, X } from "lucide-react";
import { acceptMentorship, getMyAvailability, listMyMentorRequests, rejectMentorship } from "../services/navigationApi";
import { ApiError } from "../services/httpClient";
import { useAuth } from "../context/AuthContext";
import { getPeerName } from "../services/peerNameCache";
import type { AvailabilitySlot, Mentorship } from "../types";
import { PageHeader } from "../components/ui/PageHeader";
import { Banner } from "../components/ui/Banner";
import { Spinner } from "../components/ui/Spinner";
import styles from "./MentorRequestsPage.module.css";

const STATUS_LABEL: Record<Mentorship["estado"], string> = {
  pendiente: "Pendiente",
  confirmada: "Confirmada",
  rechazada: "Rechazada",
  cancelada: "Cancelada",
  completada: "Completada",
};

function formatSlot(slot: AvailabilitySlot | undefined): string {
  if (!slot) return "Horario no disponible";
  const fecha = new Date(`${slot.fecha}T00:00:00`).toLocaleDateString("es-CO", { day: "numeric", month: "short" });
  return `${fecha} · ${slot.horaInicio.slice(0, 5)}–${slot.horaFin.slice(0, 5)}`;
}

export default function MentorRequestsPage() {
  const { accessToken } = useAuth();
  const [mentorships, setMentorships] = useState<Mentorship[]>([]);
  const [slotsById, setSlotsById] = useState<Record<string, AvailabilitySlot>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actingId, setActingId] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!accessToken) return;
    setLoading(true);
    setError(null);
    try {
      const [requests, slots] = await Promise.all([listMyMentorRequests(accessToken), getMyAvailability(accessToken)]);
      setMentorships(requests.sort((a, b) => b.creadaEn.localeCompare(a.creadaEn)));
      setSlotsById(Object.fromEntries(slots.map((s) => [s.id, s])));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No pudimos cargar tus solicitudes.");
    } finally {
      setLoading(false);
    }
  }, [accessToken]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleAccept(m: Mentorship) {
    if (!accessToken) return;
    setActingId(m.id);
    setError(null);
    try {
      const updated = await acceptMentorship(accessToken, m.id);
      setMentorships((prev) => prev.map((x) => (x.id === updated.id ? updated : x)));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No pudimos aceptar esta solicitud.");
    } finally {
      setActingId(null);
    }
  }

  async function handleReject(m: Mentorship) {
    if (!accessToken) return;
    setActingId(m.id);
    setError(null);
    try {
      const updated = await rejectMentorship(accessToken, m.id);
      setMentorships((prev) => prev.map((x) => (x.id === updated.id ? updated : x)));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No pudimos rechazar esta solicitud.");
    } finally {
      setActingId(null);
    }
  }

  const pending = mentorships.filter((m) => m.estado === "pendiente");
  const rest = mentorships.filter((m) => m.estado !== "pendiente");

  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", padding: "80px 0" }}>
        <Spinner label="Cargando solicitudes..." />
      </div>
    );
  }

  return (
    <div className={[styles.page, "fade-in"].join(" ")}>
      <PageHeader title="Solicitudes" subtitle="Mentorías pendientes de tu respuesta e historial de mentorías." />

      {error && <Banner tone="danger">{error}</Banner>}

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>
          <Inbox size={16} /> Pendientes ({pending.length})
        </h2>
        {pending.length === 0 ? (
          <p className={styles.hint}>No tienes solicitudes pendientes por ahora.</p>
        ) : (
          <div className={styles.list}>
            {pending.map((m) => (
              <div key={m.id} className={styles.item}>
                <div className={styles.itemInfo}>
                  <p className={styles.studentName}>{getPeerName(m.estudianteId, "Estudiante")}</p>
                  <p className={styles.slotText}>
                    <CalendarClock size={13} /> {formatSlot(slotsById[m.bloqueId])}
                  </p>
                </div>
                <div className={styles.itemActions}>
                  <button className={styles.acceptBtn} disabled={actingId === m.id} onClick={() => handleAccept(m)}>
                    <Check size={14} /> Aceptar
                  </button>
                  <button className={styles.rejectBtn} disabled={actingId === m.id} onClick={() => handleReject(m)}>
                    <X size={14} /> Rechazar
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Historial</h2>
        {rest.length === 0 ? (
          <p className={styles.hint}>Todavía no hay mentorías resueltas.</p>
        ) : (
          <div className={styles.list}>
            {rest.map((m) => (
              <div key={m.id} className={styles.item}>
                <div className={styles.itemInfo}>
                  <p className={styles.studentName}>{getPeerName(m.estudianteId, "Estudiante")}</p>
                  <p className={styles.slotText}>
                    <CalendarClock size={13} /> {formatSlot(slotsById[m.bloqueId])}
                  </p>
                </div>
                <span className={[styles.statusBadge, styles[m.estado]].join(" ")}>{STATUS_LABEL[m.estado]}</span>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
