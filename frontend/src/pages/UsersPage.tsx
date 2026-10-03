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

export default function UsersPage() {
  const { accessToken } = useAuth();
  const [users, setUsers] = useState<AdminUserRow[]>([]);
  const [filter, setFilter] = useState<Role | "todas">("todas");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [savingId, setSavingId] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!accessToken) return;
    setLoading(true);
    setError(null);
    try {
      const result = await listUsersWithRoles(accessToken);
      setUsers(result);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No pudimos cargar el listado de usuarios.");
    } finally {
      setLoading(false);
    }
  }, [accessToken]);

  useEffect(() => {
    load();
  }, [load]);

  async function handlePromote(user: AdminUserRow) {
    if (!accessToken) return;
    setSavingId(user.id);
    setError(null);
    try {
      const updated = await promoteToMentor(accessToken, user.id);
      setUsers((prev) => prev.map((u) => (u.id === updated.id ? updated : u)));
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
      const updated = await revertToMentee(accessToken, user.id);
      setUsers((prev) => prev.map((u) => (u.id === updated.id ? updated : u)));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No pudimos revertir el rol de este usuario.");
    } finally {
      setSavingId(null);
    }
  }

  const filtered = users.filter((u) => {
    const matchesRole = filter === "todas" || u.rol === filter;
    const matchesSearch = `${u.nombre} ${u.correo}`.toLowerCase().includes(search.toLowerCase());
    return matchesRole && matchesSearch;
  });

  return (
    <div className={styles.page}>
      <PageHeader
        title="Usuarios y roles"
        subtitle="Listado de usuarios registrados en RADIA (HU010) — promoción y reversión de roles (HU008), vía role-service."
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
              onClick={() => setFilter(f.value)}
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
              {filtered.map((u) => (
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
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={5} className={styles.empty}>
                    No se encontraron usuarios con ese criterio.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
