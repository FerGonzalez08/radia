// Panel de inicio, personalizado por rol con datos reales de los cuatro
// microservicios (antes era copy estático). Cada fetch va envuelto para no
// bloquear el resto del panel si un microservicio puntual no responde.
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  CalendarClock,
  Inbox,
  MessagesSquare,
  ShieldCheck,
  Sparkles,
  Tag,
  Users,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { ROLE_LABEL } from "../features/navigation/menuConfig";
import { listCategories, getMyAvailability, getMySettings, listMyMentorRequests, listMyStudentMentorships } from "../services/navigationApi";
import { listUsersWithRoles } from "../services/roleApi";
import styles from "./DashboardPage.module.css";

const COPY: Record<string, { headline: string; body: string }> = {
  mentee: {
    headline: "Encuentra a tu próxima mentora y sigue la conversación.",
    body: "Busca por categoría, agenda un bloque de disponibilidad y da seguimiento a tus mentorías desde un solo lugar.",
  },
  mentor: {
    headline: "Gracias por acompañar a la próxima generación de ingenieras.",
    body: "Revisa tus solicitudes pendientes, gestiona tu disponibilidad y conversa en tiempo real con tus mentees.",
  },
  admin: {
    headline: "Panel de administración del núcleo de RADIA.",
    body: "Gestiona usuarios, roles y el catálogo de categorías que conecta a mentees con mentoras.",
  },
};

interface MenteeStats {
  pendientes: number;
  confirmadas: number;
}

interface MentorStats {
  pendientes: number;
  confirmadas: number;
  bloquesLibres: number;
  autoAceptar: boolean;
}

interface AdminStats {
  usuarios: number;
  mentoras: number;
  categorias: number;
}

export default function DashboardPage() {
  const { user, accessToken } = useAuth();
  const [menteeStats, setMenteeStats] = useState<MenteeStats | null>(null);
  const [mentorStats, setMentorStats] = useState<MentorStats | null>(null);
  const [adminStats, setAdminStats] = useState<AdminStats | null>(null);

  useEffect(() => {
    if (!user || !accessToken) return;

    if (user.rol === "mentee") {
      listMyStudentMentorships(accessToken)
        .then((list) =>
          setMenteeStats({
            pendientes: list.filter((m) => m.estado === "pendiente").length,
            confirmadas: list.filter((m) => m.estado === "confirmada").length,
          }),
        )
        .catch(() => setMenteeStats({ pendientes: 0, confirmadas: 0 }));
    }

    if (user.rol === "mentor") {
      Promise.allSettled([listMyMentorRequests(accessToken), getMyAvailability(accessToken), getMySettings(accessToken)]).then(
        ([requests, availability, settings]) => {
          const list = requests.status === "fulfilled" ? requests.value : [];
          const slots = availability.status === "fulfilled" ? availability.value : [];
          setMentorStats({
            pendientes: list.filter((m) => m.estado === "pendiente").length,
            confirmadas: list.filter((m) => m.estado === "confirmada").length,
            bloquesLibres: slots.filter((s) => s.estado === "libre").length,
            autoAceptar: settings.status === "fulfilled" ? settings.value.autoAceptar : false,
          });
        },
      );
    }

    if (user.rol === "admin") {
      Promise.allSettled([listUsersWithRoles(accessToken), listCategories(accessToken)]).then(([users, categories]) => {
        const userList = users.status === "fulfilled" ? users.value : [];
        const categoryList = categories.status === "fulfilled" ? categories.value : [];
        setAdminStats({
          usuarios: userList.length,
          mentoras: userList.filter((u) => u.rol === "mentor").length,
          categorias: categoryList.length,
        });
      });
    }
  }, [user, accessToken]);

  if (!user) return null;
  const copy = COPY[user.rol] ?? COPY.mentee;
  const firstName = user.nombre.split(" ")[0];

  return (
    <div className={styles.page}>
      <section className={styles.hero}>
        <p className={styles.eyebrow}>
          <Sparkles size={13} /> {ROLE_LABEL[user.rol]}
        </p>
        <h1>Hola, {firstName}</h1>
        <hr className={styles.heroRule} />
        <p className={styles.headline}>{copy.headline}</p>
        <p className={styles.body}>{copy.body}</p>
        <Link to={user.rol === "mentee" ? "/app/mentores" : "/app/chat"} className={styles.cta}>
          {user.rol === "mentee" ? "Buscar mentor" : "Ir al chat"} <ArrowRight size={16} />
        </Link>
      </section>

      {user.rol === "mentee" && menteeStats && (
        <section className={styles.statsBox}>
          <div className={styles.statRow}>
            <p className={styles.statValue}>{menteeStats.confirmadas}</p>
            <p className={styles.statLabel}>Mentorías confirmadas</p>
          </div>
          <div className={styles.statRow}>
            <p className={styles.statValue}>{menteeStats.pendientes}</p>
            <p className={styles.statLabel}>Solicitudes pendientes</p>
          </div>
        </section>
      )}

      {user.rol === "mentor" && mentorStats && (
        <section className={styles.statsBox}>
          <div className={styles.statRow}>
            <p className={styles.statValue}>{mentorStats.pendientes}</p>
            <p className={styles.statLabel}>Solicitudes pendientes</p>
          </div>
          <div className={styles.statRow}>
            <p className={styles.statValue}>{mentorStats.confirmadas}</p>
            <p className={styles.statLabel}>Mentorías confirmadas</p>
          </div>
          <div className={styles.statRow}>
            <p className={styles.statValue}>{mentorStats.bloquesLibres}</p>
            <p className={styles.statLabel}>Bloques libres</p>
          </div>
          <div className={styles.statRow}>
            <p className={styles.statValue}>{mentorStats.autoAceptar ? "Sí" : "No"}</p>
            <p className={styles.statLabel}>Aceptación automática</p>
          </div>
        </section>
      )}

      {user.rol === "admin" && adminStats && (
        <section className={styles.statsBox}>
          <div className={styles.statRow}>
            <p className={styles.statValue}>{adminStats.usuarios}</p>
            <p className={styles.statLabel}>Usuarios registrados</p>
          </div>
          <div className={styles.statRow}>
            <p className={styles.statValue}>{adminStats.mentoras}</p>
            <p className={styles.statLabel}>Mentoras activas</p>
          </div>
          <div className={styles.statRow}>
            <p className={styles.statValue}>{adminStats.categorias}</p>
            <p className={styles.statLabel}>Categorías</p>
          </div>
        </section>
      )}

      <section className={styles.list}>
        {user.rol === "mentee" && (
          <>
            <Link to="/app/mentores" className={styles.listRow}>
              <Users size={18} className={styles.listIcon} />
              <div className={styles.listBody}>
                <h3>Buscar mentor</h3>
                <p>Filtra por categoría, revisa disponibilidad real y solicita un bloque.</p>
              </div>
              <ArrowRight size={16} className={styles.listArrow} />
            </Link>
            <Link to="/app/mis-mentorias" className={styles.listRow}>
              <CalendarClock size={18} className={styles.listIcon} />
              <div className={styles.listBody}>
                <h3>Mis mentorías</h3>
                <p>Revisa el estado de tus solicitudes y mentorías confirmadas.</p>
              </div>
              <ArrowRight size={16} className={styles.listArrow} />
            </Link>
          </>
        )}

        {user.rol === "mentor" && (
          <>
            <Link to="/app/solicitudes" className={styles.listRow}>
              <Inbox size={18} className={styles.listIcon} />
              <div className={styles.listBody}>
                <h3>Solicitudes</h3>
                <p>Acepta o rechaza mentorías pendientes de tu respuesta.</p>
              </div>
              <ArrowRight size={16} className={styles.listArrow} />
            </Link>
            <Link to="/app/disponibilidad" className={styles.listRow}>
              <CalendarClock size={18} className={styles.listIcon} />
              <div className={styles.listBody}>
                <h3>Mi disponibilidad</h3>
                <p>Gestiona tus categorías, bloques de horario y aceptación automática.</p>
              </div>
              <ArrowRight size={16} className={styles.listArrow} />
            </Link>
          </>
        )}

        <Link to="/app/chat" className={styles.listRow}>
          <MessagesSquare size={18} className={styles.listIcon} />
          <div className={styles.listBody}>
            <h3>Chat en tiempo real</h3>
            <p>Mensajería instantánea con historial, presencia y confirmaciones de entrega.</p>
          </div>
          <ArrowRight size={16} className={styles.listArrow} />
        </Link>

        {user.rol === "admin" && (
          <>
            <Link to="/app/usuarias" className={styles.listRow}>
              <Users size={18} className={styles.listIcon} />
              <div className={styles.listBody}>
                <h3>Usuarios y roles</h3>
                <p>Consulta el listado de mentees y mentoras, y gestiona la asignación de roles.</p>
              </div>
              <ArrowRight size={16} className={styles.listArrow} />
            </Link>
            <Link to="/app/categorias" className={styles.listRow}>
              <Tag size={18} className={styles.listIcon} />
              <div className={styles.listBody}>
                <h3>Categorías</h3>
                <p>Administra el catálogo que usan mentoras y mentees para encontrarse.</p>
              </div>
              <ArrowRight size={16} className={styles.listArrow} />
            </Link>
            <Link to="/app/permisos" className={styles.listRow}>
              <ShieldCheck size={18} className={styles.listIcon} />
              <div className={styles.listBody}>
                <h3>Matriz de permisos</h3>
                <p>Documentación de los permisos habilitados para cada rol en cada endpoint.</p>
              </div>
              <ArrowRight size={16} className={styles.listArrow} />
            </Link>
          </>
        )}
      </section>
    </div>
  );
}
