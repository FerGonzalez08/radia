// RQF-027/RQF-028 - Buscar mentoras por categoría, revisar su disponibilidad
// real y solicitar un bloque (navigation-service). Solo para mentees.
import { useCallback, useEffect, useState } from "react";
import { CalendarClock, CheckCircle2, ChevronDown, ChevronUp, Search, Sparkles } from "lucide-react";
import { getMentorAvailability, listCategories, requestMentorship, searchMentorsByCategory } from "../services/navigationApi";
import { ApiError } from "../services/httpClient";
import { useAuth } from "../context/AuthContext";
import { cacheMentorshipSlot, cachePeerNames } from "../services/peerNameCache";
import type { AvailabilitySlot, Category, MentorSearchResult } from "../types";
import { PageHeader } from "../components/ui/PageHeader";
import { Banner } from "../components/ui/Banner";
import { Spinner } from "../components/ui/Spinner";
import styles from "./MentorSearchPage.module.css";

function formatFecha(iso: string): string {
  const d = new Date(`${iso}T00:00:00`);
  return d.toLocaleDateString("es-CO", { weekday: "long", day: "numeric", month: "short" });
}

function formatHora(hhmmss: string): string {
  return hhmmss.slice(0, 5);
}

export default function MentorSearchPage() {
  const { accessToken } = useAuth();
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<Category | null>(null);
  const [results, setResults] = useState<MentorSearchResult[]>([]);
  const [loadingResults, setLoadingResults] = useState(false);
  const [expandedMentor, setExpandedMentor] = useState<string | null>(null);
  const [slotsByMentor, setSlotsByMentor] = useState<Record<string, AvailabilitySlot[]>>({});
  const [loadingSlotsFor, setLoadingSlotsFor] = useState<string | null>(null);
  const [requestingSlot, setRequestingSlot] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken) return;
    listCategories(accessToken).catch(() => undefined).then((cats) => cats && setCategories(cats));
  }, [accessToken]);

  const handleSelectCategory = useCallback(
    async (cat: Category) => {
      if (!accessToken) return;
      setSelectedCategory(cat);
      setResults([]);
      setExpandedMentor(null);
      setError(null);
      setLoadingResults(true);
      try {
        const found = await searchMentorsByCategory(accessToken, cat.id);
        setResults(found);
        cachePeerNames(found.map((r) => ({ id: r.mentorUserId, nombre: r.nombre })));
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "No pudimos buscar mentoras en esta categoría.");
      } finally {
        setLoadingResults(false);
      }
    },
    [accessToken],
  );

  async function toggleAvailability(mentorId: string) {
    if (expandedMentor === mentorId) {
      setExpandedMentor(null);
      return;
    }
    setExpandedMentor(mentorId);
    if (slotsByMentor[mentorId] || !accessToken) return;
    setLoadingSlotsFor(mentorId);
    try {
      const slots = await getMentorAvailability(accessToken, mentorId);
      setSlotsByMentor((prev) => ({ ...prev, [mentorId]: slots }));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No pudimos cargar la disponibilidad de esta mentora.");
    } finally {
      setLoadingSlotsFor(null);
    }
  }

  async function handleRequest(mentor: MentorSearchResult, slot: AvailabilitySlot) {
    if (!accessToken) return;
    setRequestingSlot(slot.id);
    setError(null);
    setSuccessMsg(null);
    try {
      const mentorship = await requestMentorship(accessToken, slot.id);
      cacheMentorshipSlot(mentorship.id, { fecha: slot.fecha, horaInicio: slot.horaInicio, horaFin: slot.horaFin });
      setSlotsByMentor((prev) => ({
        ...prev,
        [mentor.mentorUserId]: (prev[mentor.mentorUserId] ?? []).filter((s) => s.id !== slot.id),
      }));
      setSuccessMsg(
        mentorship.estado === "confirmada"
          ? `¡Listo! ${mentor.nombre} confirmó automáticamente tu mentoría del ${formatFecha(slot.fecha)}.`
          : `Solicitud enviada a ${mentor.nombre} para el ${formatFecha(slot.fecha)}. Te avisaremos cuando responda.`,
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No pudimos solicitar este bloque.");
    } finally {
      setRequestingSlot(null);
    }
  }

  return (
    <div className={styles.page}>
      <PageHeader
        title="Buscar mentor"
        subtitle="Filtra por categoría, revisa la disponibilidad real de cada mentora y solicita un bloque (RQF-027/RQF-028)."
      />

      {error && <Banner tone="danger">{error}</Banner>}
      {successMsg && <Banner tone="success">{successMsg}</Banner>}

      <div className={styles.categoryRow}>
        {categories.map((cat) => (
          <button
            key={cat.id}
            className={[styles.categoryPill, selectedCategory?.id === cat.id ? styles.categoryPillActive : ""].join(" ")}
            onClick={() => handleSelectCategory(cat)}
          >
            {cat.nombre}
          </button>
        ))}
        {categories.length === 0 && <p className={styles.muted}>Cargando categorías…</p>}
      </div>

      {!selectedCategory && (
        <div className={styles.emptyState}>
          <Search size={22} />
          <p>Elige una categoría para ver mentoras disponibles.</p>
        </div>
      )}

      {selectedCategory && loadingResults && (
        <div style={{ display: "flex", justifyContent: "center", padding: "40px 0" }}>
          <Spinner label="Buscando mentoras..." />
        </div>
      )}

      {selectedCategory && !loadingResults && results.length === 0 && (
        <div className={styles.emptyState}>
          <Sparkles size={22} />
          <p>Todavía no hay mentoras publicadas en "{selectedCategory.nombre}".</p>
        </div>
      )}

      <div className={styles.mentorList}>
        {results.map((mentor) => {
          const expanded = expandedMentor === mentor.mentorUserId;
          const slots = slotsByMentor[mentor.mentorUserId];
          return (
            <div className={styles.mentorCard} key={mentor.mentorUserId}>
              <button className={styles.mentorHeader} onClick={() => toggleAvailability(mentor.mentorUserId)}>
                <span className={styles.mentorAvatar}>{mentor.nombre[0]}</span>
                <div className={styles.mentorInfo}>
                  <p className={styles.mentorName}>{mentor.nombre}</p>
                  <div className={styles.mentorTags}>
                    {mentor.categorias.map((c) => (
                      <span key={c} className={styles.tag}>
                        {c}
                      </span>
                    ))}
                  </div>
                </div>
                {expanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
              </button>

              {expanded && (
                <div className={styles.slotsPanel}>
                  {loadingSlotsFor === mentor.mentorUserId ? (
                    <Spinner label="Cargando disponibilidad..." />
                  ) : slots && slots.length > 0 ? (
                    <ul className={styles.slotList}>
                      {slots.map((slot) => (
                        <li key={slot.id} className={styles.slotItem}>
                          <span className={styles.slotWhen}>
                            <CalendarClock size={14} /> {formatFecha(slot.fecha)} · {formatHora(slot.horaInicio)}–
                            {formatHora(slot.horaFin)}
                          </span>
                          <button
                            className={styles.slotBtn}
                            disabled={requestingSlot === slot.id}
                            onClick={() => handleRequest(mentor, slot)}
                          >
                            <CheckCircle2 size={14} /> Solicitar
                          </button>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className={styles.muted}>Esta mentora no tiene bloques libres por ahora.</p>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
