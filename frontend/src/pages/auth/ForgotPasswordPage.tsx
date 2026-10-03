import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { Mail } from "lucide-react";
import { AuthLayout } from "../../components/layout/AuthLayout";
import { TextField } from "../../components/ui/TextField";
import { Button } from "../../components/ui/Button";
import { Banner } from "../../components/ui/Banner";
import { useAuth } from "../../context/AuthContext";
import styles from "./AuthForms.module.css";

export default function ForgotPasswordPage() {
  const { requestPasswordReset } = useAuth();
  const [correo, setCorreo] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const result = await requestPasswordReset(correo);
      setMessage(result.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout
      eyebrow="Recuperar acceso"
      title="¿Olvidaste tu contraseña?"
      subtitle="Ingresa tu correo y te enviaremos un enlace de restablecimiento."
      footer={
        <p>
          <Link to="/iniciar-sesion">← Volver a iniciar sesión</Link>
        </p>
      }
    >
      {message ? (
        <Banner tone="success">{message}</Banner>
      ) : (
        <form className={styles.form} onSubmit={handleSubmit} noValidate>
          <TextField
            label="Correo electrónico"
            type="email"
            placeholder="nombre@correo.com"
            icon={<Mail size={16} />}
            value={correo}
            onChange={(e) => setCorreo(e.target.value)}
            required
          />
          <Button type="submit" size="lg" fullWidth loading={loading}>
            Enviar enlace de recuperación
          </Button>
        </form>
      )}
    </AuthLayout>
  );
}
