import type { ReactNode } from "react";
import { AlertTriangle, CheckCircle2, Info, XCircle } from "lucide-react";
import styles from "./Banner.module.css";

type Tone = "success" | "warning" | "danger" | "info";

const ICONS: Record<Tone, typeof Info> = {
  success: CheckCircle2,
  warning: AlertTriangle,
  danger: XCircle,
  info: Info,
};

interface BannerProps {
  tone?: Tone;
  title?: string;
  children: ReactNode;
  action?: ReactNode;
}

export function Banner({ tone = "info", title, children, action }: BannerProps) {
  const Icon = ICONS[tone];
  return (
    <div className={[styles.banner, styles[tone]].join(" ")} role={tone === "danger" ? "alert" : "status"}>
      <Icon size={18} className={styles.icon} />
      <div className={styles.content}>
        {title && <p className={styles.title}>{title}</p>}
        <div className={styles.body}>{children}</div>
      </div>
      {action && <div className={styles.action}>{action}</div>}
    </div>
  );
}
