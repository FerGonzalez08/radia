// RQF-025/RQF-026/RQF-031 - Panel de la mentora: categorías en las que
// ofrece mentoría, bloques de disponibilidad y configuración de aceptación
// automática (navigation-service). Solo para el rol mentor.
import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Plus, Tag, Trash2 } from "lucide-react";
import {
  createAvailabilitySlot,
  deleteAvailabilitySlot,
  getMyAvailability,
  getMyCategories,
  getMySettings,
  listCategories,
  setMyCategories,
  updateMySettings,
} from "../services/navigationApi";
import { ApiError } from "../services/httpClient";
import { useAuth } from "../context/AuthContext";
import type { AvailabilitySlot, Category, MentorSettings } from "../types";
import { PageHeader } from "../components/ui/PageHeader";
import { Banner } from "../components/ui/Banner";
import { Spinner } from "../components/ui/Spinner";
import styles from "./AvailabilityPage.module.css";

function formatFecha(iso: string): string {
  return new Date(`${iso}T00:00:00`).toLocaleDateString("es-CO", { weekday: "short", day: "numeric", month: "short" });
}

export default function AvailabilityPage() {
  const { accessToken } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [allCategories, setAllCategories] = useState<Category[]>([]);
  const [myCategoryIds, setMyCategoryIds] = useState<Set<string>>(new Set());
  const [savingCategories, setSavingCategories] = useState(false);

  const [settings, setSettings] = useState<MentorSettings | null>(null);
  const [savingSettings, setSavingSettings] = useState(false);

  const [slots, setSlots] = useState<AvailabilitySlot[]>([]);
  const [fecha, setFecha] = useState("");
  const [horaInicio, setHoraInicio] = useState("");
  const [horaFin, setHoraFin] = useState("");
  const [creatingSlot, setCreatingSlot] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!accessToken) return;
    setLoading(true);
    setError(null);
    try {
      const [all, mine, mySettings, mySlots] = await Promise.all([
        listCategories(accessToken),
        getMyCategories(accessToken),
        getMySettings(accessToken),
        getMyAvailability(accessToken),
      ]);
      setAllCategories(all);
      setMyCategoryIds(new Set(mine.map((c) => c.id)));
      setSettings(mySettings);
      setSlots(mySlots.sort((a, b) => (a.fecha + a.horaInicio).localeCompare(b.fecha + b.horaInicio)));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No pudimos cargar tu panel de disponibilidad.");
    } finally {
      setLoading(false);
    }
  }, [accessToken]);

  useEffect(() => {
    load();
  }, [load]);

  function toggleCategory(id: string) {
    setMyCategoryIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function handleSaveCategories() {
    if (!accessToken) return;
    setSavingCategories(true);
    setError(null);
    try {
      await setMyCategories(accessToken, Array.from(myCategoryIds));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No pudimos guardar tus categorías.");
    } finally {
      setSavingCategories(false);
    }
  }

  async function handleToggleAutoAccept() {
    if (!accessToken || !settings) return;
    setSavingSettings(true);
    setError(null);
    try {
      const updated = await updateMySettings(accessToken, !settings.autoAceptar);
      setSettings(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No pudimos actualizar tu configuración.");
    } finally {
      setSavingSettings(false);
    }
  }

  async function handleCreateSlot(e: FormEvent) {
    e.preventDefault();
    if (!accessToken || !fecha || !horaInicio || !horaFin) return;
    setCreatingSlot(true);
    setError(null);
    try {
      const slot = await createAvailabilitySlot(accessToken, fecha, horaInicio, horaFin);
      setSlots((prev) => [...prev, slot].sort((a, b) => (a.fecha + a.horaInicio).localeCompare(b.fecha + b.horaInicio)));
      setFecha("");
      setHoraInicio("");
      setHoraFin("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No pudimos crear este bloque de disponibilidad.");
    } finally {
      setCreatingSlot(false);
    }
  }

  async function handleDeleteSlot(slot: AvailabilitySlot) {
    if (!accessToken) return;
    setDeletingId(slot.id);
    setError(null);
    try {
      await deleteAvailabilitySlot(accessToken, slot.id);
      setSlots((prev) => prev.filter((s) => s.id !== slot.id));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No pudimos eliminar este bloque.");
    } finally {
      setDeletingId(null);
    }
  }

  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", padding: "80px 0" }}>
        <Spinner label="Cargando tu panel..." />
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <PageHeader
        title="Mi disponibilidad"
        subtitle="Categorías en las que ofreces mentoría, tus bloques de horario y la aceptación automática de solicitudes."
      />

      {error && <Banner tone="danger">{error}</Banner>}

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>
          <Tag size={16} /> Mis categorías
        </h2>
        <p className={styles.sectionHint}>Los mentees te encontrarán al buscar por estas categorías.</p>
        <div className={styles.categoryGrid}>
          {allCategories.map((cat) => (
            <label key={cat.id} className={styles.categoryOption}>
              <input type="checkbox" checked={myCategoryIds.has(cat.id)} onChange={() => toggleCategory(cat.id)} />
              {cat.nombre}
            </label>
          ))}
        </div>
        <button className={styles.saveBtn} onClick={handleSaveCategories} disabled={savingCategories}>
          Guardar categorías
        </button>
      </section>

      {settings && (
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Aceptación de solicitudes</h2>
          <label className={styles.toggleRow}>
            <input type="checkbox" checked={settings.autoAceptar} onChange={handleToggleAutoAccept} disabled={savingSettings} />
            Aceptar automáticamente las solicitudes de mentoría
          </label>
          <p className={styles.sectionHint}>
            Límite de mentorías confirmadas por semana: <strong>{settings.limiteSemanal}</strong>
          </p>
        </section>
      )}

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Mis bloques de disponibilidad</h2>
        <form className={styles.slotForm} onSubmit={handleCreateSlot}>
          <input className={styles.input} type="date" value={fecha} onChange={(e) => setFecha(e.target.value)} required />
          <input className={styles.input} type="time" value={horaInicio} onChange={(e) => setHoraInicio(e.target.value)} required />
          <input className={styles.input} type="time" value={horaFin} onChange={(e) => setHoraFin(e.target.value)} required />
          <button className={styles.createBtn} type="submit" disabled={creatingSlot}>
            <Plus size={16} /> Agregar
          </button>
        </form>

        <ul className={styles.slotList}>
          {slots.map((slot) => (
            <li key={slot.id} className={styles.slotItem}>
              <span className={styles.slotWhen}>
                {formatFecha(slot.fecha)} · {slot.horaInicio.slice(0, 5)}–{slot.horaFin.slice(0, 5)}
              </span>
              <span className={[styles.slotStatus, slot.estado === "libre" ? styles.slotLibre : styles.slotReservado].join(" ")}>
                {slot.estado === "libre" ? "Libre" : "Reservado"}
              </span>
              <button
                className={styles.deleteBtn}
                disabled={deletingId === slot.id}
                onClick={() => handleDeleteSlot(slot)}
                title="Eliminar bloque"
              >
                <Trash2 size={14} />
              </button>
            </li>
          ))}
          {slots.length === 0 && <p className={styles.sectionHint}>Todavía no has creado bloques de disponibilidad.</p>}
        </ul>
      </section>
    </div>
  );
}
