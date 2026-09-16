import { useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Lock, Mail } from "lucide-react";
import { AuthLayout } from "../../components/layout/AuthLayout";
import { TextField } from "../../components/ui/TextField";
import { Button } from "../../components/ui/Button";
import { Banner } from "../../components/ui/Banner";
import { useAuth } from "../../context/AuthContext";
import { ApiError } from "../../services/api";
import styles from "./AuthForms.module.css";

interface LocationState {
  from?: { pathname: string };
}

export default function LoginPage() {
  const { login, sessionNotice, clearSessionNotice, consumeExplicitLogoutFlag } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [correo, setCorreo] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [needsVerification, setNeedsVerification] = useState(false);
  const [loading, setLoading] = useState(false);

  // Si llegamos aquí justo por un cierre de sesión manual (botón "Cerrar
  // sesión"), ProtectedRoute alcanza a redirigir con state.from = la ruta
  // que se estaba viendo (por el re-render intermedio con sesión ya nula).
  // Eso es correcto para HU014 (usuaria sin sesión que intenta una ruta
  // protegida), pero no aquí: si luego inicia sesión OTRA cuenta en el
  // mismo navegador, no debe terminar en la última pantalla de la cuenta
  // anterior. Se consume la marca de forma síncrona (inicializador perezoso
  // de useState, en el primer render) en vez de en un efecto, para que no
  // haya ninguna ventana de tiempo en la que una navegación posterior
  // pueda colarse antes de descartar el "from" viejo.
  const [ignoreFromOnce] = useState(() => consumeExplicitLogoutFlag());

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setNeedsVerification(false);
    setLoading(true);
    try {
      const user = await login(correo, password);
      const state = location.state as LocationState | null;
      const redirectTo = ignoreFromOnce ? "/app/inicio" : state?.from?.pathname ?? "/app/inicio";
      navigate(user ? redirectTo : "/app/inicio", { replace: true });
    } catch (err) {
      if (err instanceof ApiError && err.code === "NOT_VERIFIED") {
        setNeedsVerification(true);
      } else if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("No pudimos iniciar sesión. Intenta nuevamente.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout
      eyebrow="Bienvenida de nuevo"
      title="Inicia sesión"
      subtitle="Ingresa con tu correo y contraseña para continuar."
      footer={
        <p>
          ¿Aún no tienes cuenta? <Link to="/registro">Regístrate</Link>
        </p>
      }
    >
      <form className={styles.form} onSubmit={handleSubmit} noValidate>
        {sessionNotice && (
          <Banner tone="info" action={<button onClick={clearSessionNotice} className={styles.link}>Entendido</button>}>
            {sessionNotice}
          </Banner>
        )}

        {error && <Banner tone="danger">{error}</Banner>}

        {needsVerification && (
          <Banner tone="warning" title="Debes verificar tu cuenta antes de iniciar sesión">
            Te enviamos un correo con un enlace de verificación cuando te registraste. Revisa tu bandeja de entrada
            (y la carpeta de spam) y haz clic en el enlace para activar tu cuenta.
          </Banner>
        )}

        <TextField
          label="Correo electrónico"
          type="email"
          placeholder="nombre@correo.com"
          icon={<Mail size={16} />}
          value={correo}
          onChange={(e) => setCorreo(e.target.value)}
          autoComplete="email"
          required
        />

        <TextField
          label="Contraseña"
          type="password"
          placeholder="Tu contraseña"
          icon={<Lock size={16} />}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="current-password"
          required
        />

        <div className={styles.rowBetween}>
          <span />
          <Link to="/recuperar-contrasena" className={styles.link}>
            ¿Olvidaste tu contraseña?
          </Link>
        </div>

        <Button type="submit" size="lg" fullWidth loading={loading}>
          Iniciar sesión
        </Button>
      </form>
    </AuthLayout>
  );
}
