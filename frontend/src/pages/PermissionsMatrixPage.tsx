import { Check, X } from "lucide-react";
import { PageHeader } from "../components/ui/PageHeader";
import styles from "./UsersPage.module.css";

interface Row {
  endpoint: string;
  descripcion: string;
  mentee: boolean;
  mentor: boolean;
  admin: boolean;
}

const ROWS: Row[] = [
  { endpoint: "POST /auth/registro", descripcion: "Crear cuenta nueva", mentee: true, mentor: true, admin: false },
  { endpoint: "POST /auth/login", descripcion: "Iniciar sesión", mentee: true, mentor: true, admin: true },
  { endpoint: "GET /usuarias", descripcion: "Listar usuarias por rol", mentee: false, mentor: false, admin: true },
  { endpoint: "PATCH /usuarias/:id/rol", descripcion: "Asignar rol manualmente", mentee: false, mentor: false, admin: true },
  { endpoint: "GET /chat/conversaciones", descripcion: "Ver conversaciones propias", mentee: true, mentor: true, admin: true },
  { endpoint: "POST /chat/mensajes", descripcion: "Enviar mensajes", mentee: true, mentor: true, admin: false },
  { endpoint: "GET /navegacion/menu", descripcion: "Obtener menú dinámico", mentee: true, mentor: true, admin: true },
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
        subtitle="Documentación de los roles autorizados por endpoint (HU011), conforme al modelo RBAC de NIST referenciado en el RQNF de seguridad."
      />

      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Endpoint</th>
              <th>Descripción</th>
              <th style={{ textAlign: "center" }}>Mentee</th>
              <th style={{ textAlign: "center" }}>Mentora</th>
              <th style={{ textAlign: "center" }}>Admin</th>
            </tr>
          </thead>
          <tbody>
            {ROWS.map((row) => (
              <tr key={row.endpoint}>
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
