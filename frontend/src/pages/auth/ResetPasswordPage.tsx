import { useState, type FormEvent } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { AuthLayout } from "../../components/layout/AuthLayout";
import { TextField } from "../../components/ui/TextField";
import { Button } from "../../components/ui/Button";
import { Banner } from "../../components/ui/Banner";
import { useAuth } from "../../context/AuthContext";
import { ApiError } from "../../services/api";
import { getPasswordError } from "../../features/auth/validators";
import styles from "./AuthForms.module.css";

export default function ResetPasswordPage() {
  const { resetPassword } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const token = params.get("token") ?? "";

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);

    const passErr = getPasswordError(password);
    if (passErr) return setError(passErr);
    if (password !== confirm) return setError("Las contraseñas no coinciden");

    setLoading(true);
    try {
      await resetPassword(token, password);
      navigate("/iniciar-sesion", { state: { passwordReset: true } });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No pudimos restablecer tu contraseña.");
    } finally {
      setLoading(false);
    }
  }

  if (!token) {
    return (
      <AuthLayout eyebrow="Enlace inválido" title="Este enlace no es válido">
        <Banner tone="danger">Solicita un nuevo enlace de recuperación.</Banner>
        <Link to="/recuperar-contrasena" className={styles.link}>
          Solicitar nuevo enlace →
        </Link>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout eyebrow="Nueva contraseña" title="Restablece tu contraseña" subtitle="Elige una contraseña nueva y segura.">
      <form className={styles.form} onSubmit={handleSubmit} noValidate>
        {error && <Banner tone="danger">{error}</Banner>}
        <TextField
          label="Nueva contraseña"
          type="password"
          placeholder="Mínimo 8 caracteres alfanuméricos"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <TextField
          label="Confirmar contraseña"
          type="password"
          placeholder="Repite tu nueva contraseña"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          required
        />
        <Button type="submit" size="lg" fullWidth loading={loading}>
          Restablecer contraseña
        </Button>
      </form>
    </AuthLayout>
  );
}
