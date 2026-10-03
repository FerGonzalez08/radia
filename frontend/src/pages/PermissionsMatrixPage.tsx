import { Check, X } from "lucide-react";
import { PageHeader } from "../components/ui/PageHeader";
import styles from "./UsersPage.module.css";

interface Row {
  servicio: string;
  endpoint: string;
  descripcion: string;
  mentee: boolean;
  mentor: boolean;
  admin: boolean;
}

// Matriz real, alineada a los endpoints de los 4 microservicios (HU011 /
// RQNF de seguridad, modelo RBAC). "mentee"/"mentor" en esta tabla incluyen
// los endpoints "/me/..." (actúan sobre la propia sesión, no requieren un
// rol distinto al dueño del recurso).
const ROWS: Row[] = [
  { servicio: "auth", endpoint: "POST /auth/register", descripcion: "Crear cuenta nueva (siempre como mentee)", mentee: true, mentor: true, admin: true },
  { servicio: "auth", endpoint: "POST /auth/login", descripcion: "Iniciar sesión", mentee: true, mentor: true, admin: true },
  { servicio: "auth", endpoint: "GET /auth/me", descripcion: "Ver mi perfil", mentee: true, mentor: true, admin: true },
  { servicio: "role", endpoint: "GET /roles/users", descripcion: "Listar usuarios con su rol", mentee: false, mentor: false, admin: true },
  { servicio: "role", endpoint: "POST /roles/:id/promote", descripcion: "Promover un mentee a mentor", mentee: false, mentor: false, admin: true },
  { servicio: "role", endpoint: "POST /roles/:id/revert", descripcion: "Revertir un mentor a mentee", mentee: false, mentor: false, admin: true },
  { servicio: "navigation", endpoint: "GET /categories", descripcion: "Ver catálogo de categorías", mentee: true, mentor: true, admin: true },
  { servicio: "navigation", endpoint: "POST/PUT/DELETE /categories", descripcion: "Administrar el catálogo de categorías", mentee: false, mentor: false, admin: true },
  { servicio: "navigation", endpoint: "GET/PUT /mentors/me/categories", descripcion: "Elegir mis propias categorías", mentee: false, mentor: true, admin: false },
  { servicio: "navigation", endpoint: "GET /search/mentors", descripcion: "Buscar mentoras por categoría", mentee: true, mentor: false, admin: false },
  { servicio: "navigation", endpoint: "GET/POST/DELETE /mentors/me/availability", descripcion: "Gestionar mi disponibilidad", mentee: false, mentor: true, admin: false },
  { servicio: "navigation", endpoint: "GET /mentors/:id/availability", descripcion: "Ver bloques libres de una mentora", mentee: true, mentor: false, admin: false },
  { servicio: "navigation", endpoint: "POST /mentorships", descripcion: "Solicitar una mentoría", mentee: true, mentor: false, admin: false },
  { servicio: "navigation", endpoint: "POST /mentorships/:id/accept|reject", descripcion: "Responder una solicitud", mentee: false, mentor: true, admin: false },
  { servicio: "navigation", endpoint: "POST /mentorships/:id/cancel", descripcion: "Cancelar una mentoría propia", mentee: true, mentor: true, admin: false },
  { servicio: "chat", endpoint: "GET /conversations/:id/messages", descripcion: "Ver historial de una conversación propia", mentee: true, mentor: true, admin: false },
  { servicio: "chat", endpoint: "WS /ws/:id", descripcion: "Enviar/recibir mensajes en tiempo real", mentee: true, mentor: true, admin: false },
];

function Cell({ allowed }: { allowed: boolean }) {
  return allowed ? (
    <Check size={16} color="var(--color-success)" />
  ) : (
    <X size={16} color="var(--color-text-faint)" />
  );
}

export default function PermissionsMatrixPage() {
  return (
    <div className={styles.page}>
      <PageHeader
        title="Matriz de permisos"
        subtitle="Documentación de los roles autorizados por endpoint (HU011) en los 4 microservicios reales de RADIA, conforme al modelo RBAC de NIST referenciado en el RQNF de seguridad."
      />

      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Servicio</th>
              <th>Endpoint</th>
              <th>Descripción</th>
              <th style={{ textAlign: "center" }}>Mentee</th>
              <th style={{ textAlign: "center" }}>Mentor</th>
              <th style={{ textAlign: "center" }}>Admin</th>
            </tr>
          </thead>
          <tbody>
            {ROWS.map((row) => (
              <tr key={row.endpoint}>
                <td className={styles.muted} style={{ textTransform: "capitalize" }}>{row.servicio}</td>
                <td style={{ fontFamily: "var(--font-mono)", fontSize: 12.5 }}>{row.endpoint}</td>
                <td className={styles.muted}>{row.descripcion}</td>
                <td style={{ textAlign: "center" }}>
                  <Cell allowed={row.mentee} />
                </td>
                <td style={{ textAlign: "center" }}>
                  <Cell allowed={row.mentor} />
                </td>
                <td style={{ textAlign: "center" }}>
                  <Cell allowed={row.admin} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
