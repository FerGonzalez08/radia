import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { CheckCircle2, MailWarning } from "lucide-react";
import { AuthLayout } from "../../components/layout/AuthLayout";
import { Banner } from "../../components/ui/Banner";
import { Button } from "../../components/ui/Button";
import { Spinner } from "../../components/ui/Spinner";
import { useAuth } from "../../context/AuthContext";
import { ApiError } from "../../services/api";
import styles from "./AuthForms.module.css";

type Status = "verifying" | "success" | "error";

// HU002: el auth-service real verifica la cuenta por un enlace de un solo
// uso enviado por correo (no por un código de 6 dígitos) — el enlace tiene
// la forma /verify-email?token=... (ver services/auth-service/app/core/email.py
// del repo de backend), así que esta pantalla solo necesita leer el token
// de la URL y confirmarlo contra el backend al cargar.
export default function VerifyAccountPage() {
  const { verifyEmail } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const token = params.get("token") ?? "";

  const [status, setStatus] = useState<Status>(token ? "verifying" : "error");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    (async () => {
      try {
        await verifyEmail(token);
        if (!cancelled) setStatus("success");
      } catch (err) {
        if (cancelled) return;
        setStatus("error");
        setError(
          err instanceof ApiError
            ? err.message
            : "No pudimos verificar tu cuenta. Intenta nuevamente desde el enlace de tu correo.",
        );
      }
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  if (status === "verifying") {
    return (
      <AuthLayout eyebrow="Un último paso" title="Verificando tu cuenta">
        <div style={{ display: "flex", justifyContent: "center", padding: "24px 0" }}>
          <Spinner label="Confirmando tu enlace de verificación..." />
        </div>
      </AuthLayout>
    );
  }

  if (status === "success") {
    return (
      <AuthLayout eyebrow="Cuenta verificada" title="¡Todo listo!">
        <div className={styles.codeHeader}>
          <div className={styles.codeIconWrap}>
            <CheckCircle2 size={24} />
          </div>
        </div>
        <Banner tone="success" title="Verificación completada">
          Tu cuenta fue activada correctamente. Ya puedes iniciar sesión.
        </Banner>
        <Button size="lg" fullWidth style={{ marginTop: 16 }} onClick={() => navigate("/iniciar-sesion")}>
          Iniciar sesión
        </Button>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout eyebrow="Enlace inválido" title="No pudimos verificar tu cuenta">
      <div className={styles.codeHeader}>
        <div className={styles.codeIconWrap}>
          <MailWarning size={24} />
        </div>
      </div>
      <Banner tone="danger">{error ?? "Este enlace de verificación no es válido o ya expiró."}</Banner>
      <p style={{ textAlign: "center", marginTop: 16 }}>
        <Link to="/iniciar-sesion" className={styles.link}>
          ← Volver a iniciar sesión
        </Link>
      </p>
    </AuthLayout>
  );
}
