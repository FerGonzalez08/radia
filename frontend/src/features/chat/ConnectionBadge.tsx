import { Loader2, Wifi, WifiOff } from "lucide-react";
import type { SocketConnectionState } from "../../types";
import styles from "./ConnectionBadge.module.css";

const CONFIG: Record<SocketConnectionState, { label: string; className: string }> = {
  conectado: { label: "Conectado", className: styles.online },
  conectando: { label: "Conectando…", className: styles.pending },
  reconectando: { label: "Reconectando…", className: styles.pending },
  desconectado: { label: "Sin conexión", className: styles.offline },
};

export function ConnectionBadge({ state }: { state: SocketConnectionState }) {
  const cfg = CONFIG[state];
  const Icon = state === "conectado" ? Wifi : state === "desconectado" ? WifiOff : Loader2;
  return (
    <span className={[styles.badge, cfg.className].join(" ")}>
      <Icon size={13} className={state === "reconectando" || state === "conectando" ? styles.spin : ""} />
      {cfg.label}
    </span>
  );
}
