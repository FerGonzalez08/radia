import { useCallback, useEffect, useState } from "react";
import { Calendar, History, Mail, Phone, ShieldCheck } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { ROLE_LABEL } from "../features/navigation/menuConfig";
import { PageHeader } from "../components/ui/PageHeader";
import { Banner } from "../components/ui/Banner";
import { Spinner } from "../components/ui/Spinner";
import { getRoleAuditLog } from "../services/roleApi";
import { ApiError } from "../services/httpClient";
import type { RoleAuditEntry } from "../types";
import styles from "./ProfilePage.module.css";
import tableStyles from "./UsersPage.module.css";

function formatFecha(iso: string): string {
  try {
    return new Date(iso).toLocaleString("es-CO", {
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return iso;
  }
}

/** Auditoría - Traza de cambios de rol, visible solo para el administrador. */
function AuditLog() {
  const { accessToken } = useAuth();
  const [entries, setEntries] = useState<RoleAuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!accessToken) return;
    setLoading(true);
    setError(null);
    try {
      setEntries(await getRoleAuditLog(accessToken));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No pudimos cargar el historial de cambios.");
    } finally {
      setLoading(false);
    }
  }, [accessToken]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className={styles.auditSection}>
      <div className={styles.auditHeader}>
        <History size={18} />
        <div>
          <h3 className={styles.auditTitle}>Historial de cambios de rol</h3>
          <p className={styles.auditSubtitle}>
            Cada vez que un administrador promueve o revierte el rol de alguien, queda registrado aquí.
          </p>
        </div>
      </div>

      {error && <Banner tone="danger">{error}</Banner>}

      {loading ? (
        <Spinner label="Cargando historial..." />
      ) : entries.length === 0 ? (
        <p className={styles.auditEmpty}>Todavía no se han registrado cambios de rol.</p>
      ) : (
        <div className={tableStyles.tableWrap}>
          <table className={tableStyles.table}>
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Usuario</th>
                <th>Cambio</th>
                <th>Realizado por</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry) => (
                <tr key={entry.id}>
                  <td>{formatFecha(entry.fecha)}</td>
                  <td>
                    <div className={styles.auditUser}>
                      <span className={styles.auditUserName}>{entry.usuarioNombre}</span>
                      <span className={styles.auditUserEmail}>{entry.usuarioCorreo}</span>
                    </div>
                  </td>
                  <td>
                    {entry.rolAnterior} → {entry.rolNuevo}
                  </td>
                  <td>
                    <div className={styles.auditUser}>
                      <span className={styles.auditUserName}>{entry.adminNombre}</span>
                      <span className={styles.auditUserEmail}>{entry.adminCorreo}</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default function ProfilePage() {
  const { user } = useAuth();
  if (!user) return null;

  const fields = [
    { icon: Mail, label: "Correo", value: user.correo },
    { icon: Phone, label: "Teléfono", value: user.telefono },
    { icon: Calendar, label: "Fecha de nacimiento", value: user.fechaNacimiento },
    { icon: ShieldCheck, label: "Rol", value: ROLE_LABEL[user.rol] },
  ];

  return (
    <div className={[styles.page, "fade-in"].join(" ")}>
      <PageHeader title="Mi perfil" subtitle="Información de tu cuenta en RADIA." />

      <div className={styles.card}>
        <div className={styles.identity}>
          <span className={styles.avatar} style={{ background: user.avatarColor }}>
            {user.nombre[0]}
          </span>
          <div>
            <h2 className={styles.name}>{user.nombre}</h2>
            <p className={styles.role}>{ROLE_LABEL[user.rol]}</p>
          </div>
        </div>

        <div className={styles.fields}>
          {fields.map((f) => (
            <div key={f.label} className={styles.field}>
              <f.icon size={16} />
              <div>
                <p className={styles.fieldLabel}>{f.label}</p>
                <p className={styles.fieldValue}>{f.value}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {user.rol === "admin" && <AuditLog />}
    </div>
  );
}
