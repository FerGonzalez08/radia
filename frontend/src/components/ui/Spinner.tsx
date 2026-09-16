import { Loader2 } from "lucide-react";
import styles from "./Spinner.module.css";

export function Spinner({ label }: { label?: string }) {
  return (
    <div className={styles.wrap}>
      <Loader2 className={styles.icon} size={28} />
      {label && <p className={styles.label}>{label}</p>}
    </div>
  );
}
