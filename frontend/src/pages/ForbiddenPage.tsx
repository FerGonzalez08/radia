import { Link } from "react-router-dom";
import { ShieldAlert } from "lucide-react";
import { Button } from "../components/ui/Button";
import styles from "./StatusPage.module.css";

export default function ForbiddenPage() {
  return (
    <div className={styles.page}>
      <div className={styles.iconWrap}>
        <ShieldAlert size={30} />
      </div>
      <p className={styles.code}>Error 403</p>
      <h1 className={styles.title}>No tienes permiso para ver esta sección</h1>
      <p className={styles.text}>
        Tu rol actual no tiene acceso a esta página. Si crees que esto es un error, contacta a una administradora.
      </p>
      <Link to="/app/inicio">
        <Button>Volver al inicio</Button>
      </Link>
    </div>
  );
}
