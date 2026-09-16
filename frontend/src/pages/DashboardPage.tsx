import { Link } from "react-router-dom";
import { ArrowRight, MessagesSquare, ShieldCheck, Sparkles, Users } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { ROLE_LABEL } from "../features/navigation/menuConfig";
import styles from "./DashboardPage.module.css";

const COPY: Record<string, { headline: string; body: string }> = {
  mentee: {
    headline: "Tu mentor está a un mensaje de distancia.",
    body: "Continúa la conversación con tu mentor asignado, revisa el historial de acompañamiento y mantente al tanto de sus mensajes.",
  },
  mentor: {
    headline: "Gracias por acompañar a la próxima generación de ingenieras.",
    body: "Revisa tus conversaciones activas con mentees y responde en tiempo real desde el chat de RADIA.",
  },
  admin: {
    headline: "Panel de administración del núcleo de RADIA.",
    body: "Gestiona usuarios, roles y supervisa el estado general de la plataforma.",
  },
};

export default function DashboardPage() {
  const { user } = useAuth();
  if (!user) return null;
  const copy = COPY[user.rol] ?? COPY.mentee;
  const firstName = user.nombre.split(" ")[0];

  return (
    <div className={styles.page}>
      <section className={styles.hero}>
        <p className={styles.eyebrow}>
          <Sparkles size={14} /> {ROLE_LABEL[user.rol]}
        </p>
        <h1>Hola, {firstName} 👋</h1>
        <p className={styles.headline}>{copy.headline}</p>
        <p className={styles.body}>{copy.body}</p>
        <Link to="/app/chat" className={styles.cta}>
          Ir al chat <ArrowRight size={16} />
        </Link>
      </section>

      <section className={styles.grid}>
        <Link to="/app/chat" className={styles.card}>
          <MessagesSquare size={20} />
          <h3>Chat en tiempo real</h3>
          <p>Mensajería instantánea con historial, estado de conexión y confirmaciones de entrega.</p>
        </Link>

        {user.rol === "admin" && (
          <>
            <Link to="/app/usuarias" className={styles.card}>
              <Users size={20} />
              <h3>Usuarios y roles</h3>
              <p>Consulta el listado de mentees y mentores, y gestiona la asignación de roles.</p>
            </Link>
            <Link to="/app/permisos" className={styles.card}>
              <ShieldCheck size={20} />
              <h3>Matriz de permisos</h3>
              <p>Documentación de los permisos habilitados para cada rol en cada endpoint.</p>
            </Link>
          </>
        )}
      </section>
    </div>
  );
}
