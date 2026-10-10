// Orientación académica con el agente de IA (microservicio externo del repo
// Proyecto-de-grado). Pantalla independiente del chat de mentorías.
import { PageHeader } from "../components/ui/PageHeader";
import { OrientacionChat } from "../features/orientacion/OrientacionChat";
import styles from "./OrientacionPage.module.css";

export default function OrientacionPage() {
  return (
    <div className={styles.page}>
      <PageHeader
        title="Orientación académica"
        subtitle="Conversa con el agente de IA de RADIA para recibir una orientación inicial sobre tus competencias técnicas y actitudinales."
      />
      <div className={styles.chatWrap}>
        <OrientacionChat />
      </div>
    </div>
  );
}
