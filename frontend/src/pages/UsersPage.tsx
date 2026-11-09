import { useCallback, useEffect, useState } from "react";
import { ArrowDownCircle, ArrowUpCircle, Search } from "lucide-react";
import { listUsersWithRoles, promoteToMentor, revertToMentee } from "../services/roleApi";
import { ApiError } from "../services/httpClient";
import { useAuth } from "../context/AuthContext";
import { ROLE_LABEL } from "../features/navigation/menuConfig";
import type { AdminUserRow, Role } from "../types";
import { PageHeader } from "../components/ui/PageHeader";
import { Banner } from "../components/ui/Banner";
import { Spinner } from "../components/ui/Spinner";
import styles from "./UsersPage.module.css";

const ROLE_FILTERS: Array<{ value: Role | "todas"; label: string }> = [
  { value: "todas", label: "Todas" },
  { value: "mentee", label: "Mentees" },
  { value: "mentor", label: "Mentores" },
  { value: "admin", label: "Administradores" },
];

const STATUS_LABEL: Record<AdminUserRow["estado"], string> = {
  activo: "Activo",
  pendiente: "Pendiente",
  bloqueado: "Bloqueado",
};

const PAGE_SIZE = 25;

export default function UsersPage() {
  const { accessToken } = useAuth();
  const [users, setUsers] = useState<AdminUserRow[]>([]);
  const [filter, setFilter] = useState<Role | "todas">("todas");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [savingId, setSavingId] = useState<string | null>(null);
  // TC-NFR-09: el filtro, la búsqueda y la paginación se resuelven en el servidor; se piden PAGE_SIZE + 1 filas para
  // saber si hay una página más sin traer todo el listado.
  const [limit, setLimit] = useState(PAGE_SIZE);
  const [hasMore, setHasMore] = useState(false);
  const [debouncedSearch, setDebouncedSearch] = useState("");

  useEffect(() => {
    const t = setTimeout(() => {
      setDebouncedSearch(search);
      setLimit(PAGE_SIZE);
    }, 300);
    return () => clearTimeout(t);
  }, [search]);

  const load = useCallback(async () => {
    if (!accessToken) return;
    setLoading(true);
    setError(null);
    try {
      const result = await listUsersWithRoles(accessToken, {
        q: debouncedSearch,
        rol: filter === "todas" ? undefined : filter,
        limit: limit + 1,
      });
      setHasMore(result.length > limit);
      setUsers(result.slice(0, limit));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No pudimos cargar el listado de usuarios.");
    } finally {
      setLoading(false);
    }
  }, [accessToken, debouncedSearch, filter, limit]);

  useEffect(() => {
    load();
  }, [load]);

  async function handlePromote(user: AdminUserRow) {
    if (!accessToken) return;
    setSavingId(user.id);
    setError(null);
    try {
      await promoteToMentor(accessToken, user.id);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No pudimos promover a este usuario.");
    } finally {
      setSavingId(null);
    }
  }

  async function handleRevert(user: AdminUserRow) {
    if (!accessToken) return;
    setSavingId(user.id);
    setError(null);
    try {
      await revertToMentee(accessToken, user.id);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No pudimos revertir el rol de este usuario.");
    } finally {
      setSavingId(null);
    }
  }

  return (
    <div className={[styles.page, "fade-in"].join(" ")}>
      <PageHeader
        title="Usuarios y roles"
        subtitle="Consulta los usuarios registrados en RADIA y gestiona sus roles."
      />

      {error && <Banner tone="danger">{error}</Banner>}

      <div className={styles.toolbar}>
        <div className={styles.search}>
          <Search size={16} />
          <input placeholder="Buscar por nombre o correo..." value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <div className={styles.filters}>
          {ROLE_FILTERS.map((f) => (
            <button
              key={f.value}
              className={[styles.filterBtn, filter === f.value ? styles.filterActive : ""].join(" ")}
              onClick={() => {
                setFilter(f.value);
                setLimit(PAGE_SIZE);
              }}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div style={{ display: "flex", justifyContent: "center", padding: "48px 0" }}>
          <Spinner label="Cargando usuarios..." />
        </div>
      ) : (
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Usuario</th>
                <th>Correo</th>
                <th>Rol</th>
                <th>Estado</th>
                <th>Acción</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td>
                    <div className={styles.userCell}>
                      <span className={styles.avatar} style={{ background: u.avatarColor }}>
                        {u.nombre[0]}
                      </span>
                      {u.nombre}
                    </div>
                  </td>
                  <td className={styles.muted}>{u.correo}</td>
                  <td>
                    <span className={styles.roleBadge}>{ROLE_LABEL[u.rol]}</span>
                  </td>
                  <td>
                    <span className={[styles.statusBadge, styles[u.estado]].join(" ")}>{STATUS_LABEL[u.estado]}</span>
                  </td>
                  <td>
                    {u.rol === "mentee" && (
                      <button
                        type="button"
                        className={styles.actionBtn}
                        disabled={savingId === u.id}
                        onClick={() => handlePromote(u)}
                      >
                        <ArrowUpCircle size={14} /> Promover a mentor
                      </button>
                    )}
                    {u.rol === "mentor" && (
                      <button
                        type="button"
                        className={[styles.actionBtn, styles.actionBtnMuted].join(" ")}
                        disabled={savingId === u.id}
                        onClick={() => handleRevert(u)}
                      >
                        <ArrowDownCircle size={14} /> Revertir a mentee
                      </button>
                    )}
                    {u.rol === "admin" && <span className={styles.muted}>—</span>}
                  </td>
                </tr>
              ))}
              {users.length === 0 && (
                <tr>
                  <td colSpan={5} className={styles.empty}>
                    No se encontraron usuarios con ese criterio.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
          {hasMore && (
            <div style={{ display: "flex", justifyContent: "center", padding: "16px 0" }}>
              <button type="button" className={styles.actionBtn} onClick={() => setLimit((l) => l + PAGE_SIZE)}>
                Mostrar más
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
