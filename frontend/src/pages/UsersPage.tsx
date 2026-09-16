import { useCallback, useEffect, useState } from "react";
import { Search } from "lucide-react";
import { listAllUsers, updateUserRole, ApiError } from "../services/api";
import { useAuth } from "../context/AuthContext";
import { ROLE_LABEL } from "../features/navigation/menuConfig";
import type { Role, User } from "../types";
import { PageHeader } from "../components/ui/PageHeader";
import { Banner } from "../components/ui/Banner";
import { Spinner } from "../components/ui/Spinner";
import styles from "./UsersPage.module.css";

const ROLE_FILTERS: Array<{ value: Role | "todas"; label: string }> = [
  { value: "todas", label: "Todas" },
  { value: "mentee", label: "Mentees" },
  { value: "mentor", label: "Mentoras" },
  { value: "admin", label: "Administradoras" },
];

const STATUS_LABEL: Record<User["estado"], string> = {
  activo: "Activa",
  pendiente: "Pendiente",
  bloqueado: "Bloqueada",
};

// Roles que una administradora puede asignar manualmente (HU008). El
// backend rechaza reasignar el rol de una cuenta que ya es admin, así
// que esa opción no se ofrece aquí.
const ASSIGNABLE_ROLES: Array<{ value: "mentee" | "mentor"; label: string }> = [
  { value: "mentee", label: "Mentee" },
  { value: "mentor", label: "Mentora" },
];

export default function UsersPage() {
  const { accessToken } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
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
      const result = await listAllUsers(accessToken);
      setUsers(result);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No pudimos cargar el listado de usuarias.");
    } finally {
      setLoading(false);
    }
  }, [accessToken]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleRoleChange(user: User, newRole: "mentee" | "mentor") {
    if (!accessToken || newRole === user.rol) return;
    setSavingId(user.id);
    setError(null);
    try {
      const updated = await updateUserRole(accessToken, user.id, newRole);
      setUsers((prev) => prev.map((u) => (u.id === updated.id ? updated : u)));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No pudimos actualizar el rol de esta usuaria.");
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
        title="Usuarias y roles"
        subtitle="Listado de usuarias registradas en RADIA (HU010) — asignación manual de roles (HU008) y consulta por rol (HU010)."
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
          <Spinner label="Cargando usuarias..." />
        </div>
      ) : (
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Usuaria</th>
                <th>Correo</th>
                <th>Rol</th>
                <th>Estado</th>
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
                    {u.rol === "admin" ? (
                      <span className={styles.roleBadge}>{ROLE_LABEL[u.rol]}</span>
                    ) : (
                      <select
                        className={styles.roleSelect}
                        value={u.rol}
                        disabled={savingId === u.id}
                        onChange={(e) => handleRoleChange(u, e.target.value as "mentee" | "mentor")}
                      >
                        {ASSIGNABLE_ROLES.map((r) => (
                          <option key={r.value} value={r.value}>
                            {r.label}
                          </option>
                        ))}
                      </select>
                    )}
                  </td>
                  <td>
                    <span className={[styles.statusBadge, styles[u.estado]].join(" ")}>{STATUS_LABEL[u.estado]}</span>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={4} className={styles.empty}>
                    No se encontraron usuarias con ese criterio.
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
