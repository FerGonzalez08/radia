import { Calendar, Mail, Phone, ShieldCheck } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { ROLE_LABEL } from "../features/navigation/menuConfig";
import { PageHeader } from "../components/ui/PageHeader";
import styles from "./ProfilePage.module.css";

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
    <div className={styles.page}>
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
    </div>
  );
}
