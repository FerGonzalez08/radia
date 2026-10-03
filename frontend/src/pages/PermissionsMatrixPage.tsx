import { Check, X } from "lucide-react";
import { PageHeader } from "../components/ui/PageHeader";
import styles from "./UsersPage.module.css";

interface Row {
  descripcion: string;
  mentee: boolean;
  mentor: boolean;
  admin: boolean;
}

// Qué puede hacer cada rol dentro de RADIA. Antes esta tabla mostraba el
// endpoint tecnico real detras de cada permiso (util como referencia interna
// de desarrollo) -- se deja solo la descripcion en lenguaje llano, porque
// esta pantalla la ve un administrador desde la interfaz, no un desarrollador.
const ROWS: Row[] = [
  { descripcion: "Crear una cuenta nueva", mentee: true, mentor: true, admin: true },
  { descripcion: "Iniciar sesión", mentee: true, mentor: true, admin: true },
  { descripcion: "Ver mi propio perfil", mentee: true, mentor: true, admin: true },
  { descripcion: "Ver el listado de usuarios con su rol", mentee: false, mentor: false, admin: true },
  { descripcion: "Promover una mentee a mentora", mentee: false, mentor: false, admin: true },
  { descripcion: "Revertir una mentora a mentee", mentee: false, mentor: false, admin: true },
  { descripcion: "Ver el catálogo de categorías", mentee: true, mentor: true, admin: true },
  { descripcion: "Crear, editar o eliminar categorías", mentee: false, mentor: false, admin: true },
  { descripcion: "Elegir mis propias categorías de mentoría", mentee: false, mentor: true, admin: false },
  { descripcion: "Buscar mentoras por categoría", mentee: true, mentor: false, admin: false },
  { descripcion: "Gestionar mi disponibilidad de horarios", mentee: false, mentor: true, admin: false },
  { descripcion: "Ver los bloques libres de una mentora", mentee: true, mentor: false, admin: false },
  { descripcion: "Solicitar una mentoría", mentee: true, mentor: false, admin: false },
  { descripcion: "Aceptar o rechazar una solicitud", mentee: false, mentor: true, admin: false },
  { descripcion: "Cancelar una mentoría propia", mentee: true, mentor: true, admin: false },
  { descripcion: "Ver el historial de una conversación propia", mentee: true, mentor: true, admin: false },
  { descripcion: "Enviar y recibir mensajes en tiempo real", mentee: true, mentor: true, admin: false },
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
    <div className={[styles.page, "fade-in"].join(" ")}>
      <PageHeader
        title="Permisos por rol"
        subtitle="Consulta qué puede hacer cada tipo de usuario dentro de RADIA."
      />

      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Acción</th>
              <th style={{ textAlign: "center" }}>Mentee</th>
              <th style={{ textAlign: "center" }}>Mentor</th>
              <th style={{ textAlign: "center" }}>Admin</th>
            </tr>
          </thead>
          <tbody>
            {ROWS.map((row) => (
              <tr key={row.descripcion}>
                <td>{row.descripcion}</td>
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
