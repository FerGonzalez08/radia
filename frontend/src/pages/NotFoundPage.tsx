import { Link } from "react-router-dom";
import { Compass } from "lucide-react";
import { Button } from "../components/ui/Button";
import styles from "./StatusPage.module.css";

export default function NotFoundPage() {
  return (
    <div className={styles.page}>
      <div className={styles.iconWrap}>
        <Compass size={30} />
      </div>
      <p className={styles.code}>Error 404</p>
      <h1 className={styles.title}>Esta página no existe</h1>
      <p className={styles.text}>Revisa la dirección o vuelve al inicio de RADIA.</p>
      <Link to="/">
        <Button>Ir al inicio</Button>
      </Link>
    </div>
  );
}
