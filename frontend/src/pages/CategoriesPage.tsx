// HU / RQF-024 - Catálogo de categorías de mentoría (navigation-service),
// administrado exclusivamente por el rol admin. Las mentoras seleccionan
// de este catálogo las categorías en las que ofrecen mentoría, y los
// mentees buscan por categoría (ver MentorSearchPage).
import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Pencil, Plus, Tag, Trash2, X } from "lucide-react";
import { createCategory, deleteCategory, listCategories, updateCategory } from "../services/navigationApi";
import { ApiError } from "../services/httpClient";
import { useAuth } from "../context/AuthContext";
import type { Category } from "../types";
import { PageHeader } from "../components/ui/PageHeader";
import { Banner } from "../components/ui/Banner";
import { Spinner } from "../components/ui/Spinner";
import styles from "./CategoriesPage.module.css";

export default function CategoriesPage() {
  const { accessToken } = useAuth();
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const [nombre, setNombre] = useState("");
  const [descripcion, setDescripcion] = useState("");

  const [editingId, setEditingId] = useState<string | null>(null);
  const [editNombre, setEditNombre] = useState("");
  const [editDescripcion, setEditDescripcion] = useState("");

  const load = useCallback(async () => {
    if (!accessToken) return;
    setLoading(true);
    setError(null);
    try {
      setCategories(await listCategories(accessToken));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No pudimos cargar las categorías.");
    } finally {
      setLoading(false);
    }
  }, [accessToken]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    if (!accessToken || !nombre.trim()) return;
    setSaving(true);
    setError(null);
    try {
      const created = await createCategory(accessToken, nombre, descripcion);
      setCategories((prev) => [...prev, created].sort((a, b) => a.nombre.localeCompare(b.nombre)));
      setNombre("");
      setDescripcion("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No pudimos crear la categoría.");
    } finally {
      setSaving(false);
    }
  }

  function startEdit(cat: Category) {
    setEditingId(cat.id);
    setEditNombre(cat.nombre);
    setEditDescripcion(cat.descripcion ?? "");
  }

  async function handleSaveEdit(id: string) {
    if (!accessToken) return;
    setSaving(true);
    setError(null);
    try {
      const updated = await updateCategory(accessToken, id, { nombre: editNombre, descripcion: editDescripcion || null });
      setCategories((prev) => prev.map((c) => (c.id === id ? updated : c)));
      setEditingId(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No pudimos actualizar la categoría.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(cat: Category) {
    if (!accessToken) return;
    setSaving(true);
    setError(null);
    try {
      await deleteCategory(accessToken, cat.id);
      setCategories((prev) => prev.filter((c) => c.id !== cat.id));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No pudimos eliminar la categoría.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className={[styles.page, "fade-in"].join(" ")}>
      <PageHeader
        title="Categorías de mentoría"
        subtitle="Catálogo que usan las mentoras para publicar sus áreas y los mentees para buscar por categoría."
      />

      {error && <Banner tone="danger">{error}</Banner>}

      <form className={styles.createForm} onSubmit={handleCreate}>
        <input
          className={styles.input}
          placeholder="Nombre de la categoría (ej. Ciberseguridad)"
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
          maxLength={100}
          required
        />
        <input
          className={styles.input}
          placeholder="Descripción (opcional)"
          value={descripcion}
          onChange={(e) => setDescripcion(e.target.value)}
        />
        <button className={styles.createBtn} type="submit" disabled={saving || !nombre.trim()}>
          <Plus size={16} /> Crear
        </button>
      </form>

      {loading ? (
        <div style={{ display: "flex", justifyContent: "center", padding: "48px 0" }}>
          <Spinner label="Cargando categorías..." />
        </div>
      ) : (
        <ul className={styles.list}>
          {categories.map((cat) => (
            <li key={cat.id} className={styles.item}>
              {editingId === cat.id ? (
                <>
                  <div className={styles.editFields}>
                    <input className={styles.input} value={editNombre} onChange={(e) => setEditNombre(e.target.value)} />
                    <input
                      className={styles.input}
                      value={editDescripcion}
                      onChange={(e) => setEditDescripcion(e.target.value)}
                      placeholder="Descripción"
                    />
                  </div>
                  <div className={styles.itemActions}>
                    <button className={styles.iconBtn} onClick={() => handleSaveEdit(cat.id)} disabled={saving} title="Guardar">
                      Guardar
                    </button>
                    <button className={styles.iconBtn} onClick={() => setEditingId(null)} title="Cancelar">
                      <X size={15} />
                    </button>
                  </div>
                </>
              ) : (
                <>
                  <div className={styles.itemInfo}>
                    <span className={styles.itemIcon}>
                      <Tag size={16} />
                    </span>
                    <div>
                      <p className={styles.itemName}>{cat.nombre}</p>
                      {cat.descripcion && <p className={styles.itemDesc}>{cat.descripcion}</p>}
                    </div>
                  </div>
                  <div className={styles.itemActions}>
                    <button className={styles.iconBtn} onClick={() => startEdit(cat)} title="Editar">
                      <Pencil size={15} />
                    </button>
                    <button className={styles.iconBtnDanger} onClick={() => handleDelete(cat)} title="Eliminar">
                      <Trash2 size={15} />
                    </button>
                  </div>
                </>
              )}
            </li>
          ))}
          {categories.length === 0 && <li className={styles.empty}>Todavía no hay categorías — crea la primera arriba.</li>}
        </ul>
      )}
    </div>
  );
}
