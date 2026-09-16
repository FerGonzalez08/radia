import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { Calendar, MailCheck, Mail, Phone, User as UserIcon } from "lucide-react";
import { AuthLayout } from "../../components/layout/AuthLayout";
import { TextField } from "../../components/ui/TextField";
import { SelectField } from "../../components/ui/SelectField";
import { Button } from "../../components/ui/Button";
import { Banner } from "../../components/ui/Banner";
import { Modal } from "../../components/ui/Modal";
import { useAuth } from "../../context/AuthContext";
import { ApiError } from "../../services/api";
import { getAgeError, getNameError, getPasswordError, getPhoneError, isValidEmail, passwordStrength } from "../../features/auth/validators";
import type { RegisterPayload, Sexo } from "../../types";
import styles from "./AuthForms.module.css";

type FormState = {
  nombre: string;
  correo: string;
  telefono: string;
  sexo: Sexo | "";
  fechaNacimiento: string;
  password: string;
  confirmPassword: string;
};

const EMPTY: FormState = {
  nombre: "",
  correo: "",
  telefono: "",
  sexo: "",
  fechaNacimiento: "",
  password: "",
  confirmPassword: "",
};

export default function RegisterPage() {
  const { register } = useAuth();
  const [form, setForm] = useState<FormState>(EMPTY);
  const [errors, setErrors] = useState<Partial<Record<keyof FormState, string>>>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [showTerms, setShowTerms] = useState(false);
  const [loading, setLoading] = useState(false);
  const [registeredEmail, setRegisteredEmail] = useState<string | null>(null);

  function update<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((f) => ({ ...f, [key]: value }));
    setErrors((e) => ({ ...e, [key]: undefined }));
  }

  function validate(): boolean {
    const next: Partial<Record<keyof FormState, string>> = {};
    const nameErr = getNameError(form.nombre);
    if (nameErr) next.nombre = nameErr;
    if (!isValidEmail(form.correo)) next.correo = "Ingresa un correo electrónico válido";
    const phoneErr = getPhoneError(form.telefono);
    if (phoneErr) next.telefono = phoneErr;
    if (!form.sexo) next.sexo = "Selecciona una opción";
    const ageErr = getAgeError(form.fechaNacimiento);
    if (ageErr) next.fechaNacimiento = ageErr;
    const passErr = getPasswordError(form.password);
    if (passErr) next.password = passErr;
    if (form.confirmPassword !== form.password) next.confirmPassword = "Las contraseñas no coinciden";

    setErrors(next);
    return Object.keys(next).length === 0;
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setFormError(null);
    // HU001 - Escenario 5: al finalizar el formulario y hacer click en
    // "Registro", el sistema muestra un pop-up con los Términos y Condiciones.
    if (validate()) setShowTerms(true);
  }

  async function confirmRegistration() {
    setLoading(true);
    setFormError(null);
    try {
      const payload: RegisterPayload = {
        nombre: form.nombre.trim(),
        correo: form.correo.trim(),
        password: form.password,
        telefono: form.telefono.trim(),
        sexo: form.sexo as Sexo,
        fechaNacimiento: form.fechaNacimiento,
        aceptaTerminos: true,
      };
      const result = await register(payload);
      setShowTerms(false);
      setRegisteredEmail(result.correo);
    } catch (err) {
      setShowTerms(false);
      if (err instanceof ApiError) {
        if (err.field && err.field in EMPTY) setErrors((e) => ({ ...e, [err.field as keyof FormState]: err.message }));
        else setFormError(err.message);
      } else {
        setFormError("No pudimos crear tu cuenta. Intenta nuevamente.");
      }
    } finally {
      setLoading(false);
    }
  }

  const strength = form.password ? passwordStrength(form.password) : null;

  if (registeredEmail) {
    return (
      <AuthLayout eyebrow="Un último paso" title="Revisa tu correo">
        <div className={styles.codeHeader}>
          <div className={styles.codeIconWrap}>
            <MailCheck size={24} />
          </div>
          <p style={{ color: "var(--color-text-muted)", fontSize: 14.5 }}>
            Te enviamos un enlace de verificación a <strong>{registeredEmail}</strong>
          </p>
        </div>
        <Banner tone="success" title="Cuenta creada">
          Haz clic en el enlace del correo para activar tu cuenta y poder iniciar sesión. Si no lo ves, revisa la
          carpeta de spam.
        </Banner>
        <p style={{ textAlign: "center", marginTop: 16 }}>
          <Link to="/iniciar-sesion" className={styles.link}>
            ← Volver a iniciar sesión
          </Link>
        </p>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout
      eyebrow="Crea tu cuenta"
      title="Únete a RADIA"
      subtitle="Regístrate como mentee. Los mentores se habilitan por un administrador."
      footer={
        <p>
          ¿Ya tienes cuenta? <Link to="/iniciar-sesion">Inicia sesión</Link>
        </p>
      }
    >
      <form className={styles.form} onSubmit={handleSubmit} noValidate>
        {formError && <Banner tone="danger">{formError}</Banner>}

        <TextField
          label="Nombre completo"
          placeholder="Ej. Valentina Ríos"
          icon={<UserIcon size={16} />}
          value={form.nombre}
          onChange={(e) => update("nombre", e.target.value)}
          error={errors.nombre}
          autoComplete="name"
        />

        <TextField
          label="Correo electrónico"
          type="email"
          placeholder="nombre@correo.com"
          icon={<Mail size={16} />}
          value={form.correo}
          onChange={(e) => update("correo", e.target.value)}
          error={errors.correo}
          autoComplete="email"
        />

        <div className={styles.row}>
          <TextField
            label="Teléfono"
            placeholder="300 123 4567"
            icon={<Phone size={16} />}
            value={form.telefono}
            onChange={(e) => update("telefono", e.target.value)}
            error={errors.telefono}
            autoComplete="tel"
          />
          <TextField
            label="Fecha de nacimiento"
            type="date"
            icon={<Calendar size={16} />}
            value={form.fechaNacimiento}
            onChange={(e) => update("fechaNacimiento", e.target.value)}
            error={errors.fechaNacimiento}
          />
        </div>

        <SelectField
          label="Sexo"
          value={form.sexo}
          onChange={(e) => update("sexo", e.target.value as Sexo)}
          placeholder="Selecciona una opción"
          error={errors.sexo}
          options={[
            { value: "femenino", label: "Femenino" },
            { value: "masculino", label: "Masculino" },
            { value: "prefiero_no_decir", label: "Prefiero no decir" },
          ]}
        />

        <TextField
          label="Contraseña"
          type="password"
          placeholder="Mínimo 8 caracteres alfanuméricos"
          value={form.password}
          onChange={(e) => update("password", e.target.value)}
          error={errors.password}
          hint={
            !errors.password && strength
              ? `Fortaleza: ${strength.label}`
              : "Combina letras y números, mínimo 8 caracteres"
          }
          autoComplete="new-password"
        />

        <TextField
          label="Confirmar contraseña"
          type="password"
          placeholder="Repite tu contraseña"
          value={form.confirmPassword}
          onChange={(e) => update("confirmPassword", e.target.value)}
          error={errors.confirmPassword}
          autoComplete="new-password"
        />

        <Button type="submit" size="lg" fullWidth loading={loading}>
          Registro
        </Button>
      </form>

      <Modal
        open={showTerms}
        onClose={() => !loading && setShowTerms(false)}
        title="Términos y Condiciones de RADIA"
        footer={
          <>
            <Button variant="ghost" onClick={() => setShowTerms(false)} disabled={loading}>
              Rechazar
            </Button>
            <Button onClick={confirmRegistration} loading={loading}>
              Aceptar y crear cuenta
            </Button>
          </>
        }
      >
        <h3>1. Objeto de la plataforma</h3>
        <p>
          RADIA es un ecosistema digital de mentoría del programa Women Tech UCatólica que conecta a mentees
          (estudiantes de ingeniería) con mentores (profesionales o egresadas) para acompañamiento académico y
          profesional.
        </p>
        <h3>2. Tratamiento de datos personales</h3>
        <p>
          Tus datos (nombre, correo, teléfono, fecha de nacimiento, sexo) se usan únicamente para gestionar tu
          cuenta, asignar mentorías y habilitar el chat entre usuarios verificados, conforme a la Ley 1581 de 2012
          y la Ley 527 de 1999 sobre mensajes de datos y firma digital.
        </p>
        <h3>3. Responsabilidades del usuario</h3>
        <p>
          Te comprometes a mantener un trato respetuoso dentro del chat, no compartir tus credenciales y notificar
          cualquier uso indebido de tu cuenta.
        </p>
        <h3>4. Vigencia</h3>
        <p>Estos términos aplican mientras tu cuenta permanezca activa en RADIA.</p>
      </Modal>
    </AuthLayout>
  );
}
