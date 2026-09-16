import { forwardRef, useId, useState, type InputHTMLAttributes, type ReactNode } from "react";
import { AlertCircle, Eye, EyeOff } from "lucide-react";
import styles from "./TextField.module.css";

interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string | null;
  hint?: string;
  icon?: ReactNode;
}

export const TextField = forwardRef<HTMLInputElement, TextFieldProps>(function TextField(
  { label, error, hint, icon, id, type = "text", className, ...rest },
  ref,
) {
  const autoId = useId();
  const fieldId = id ?? autoId;
  const isPassword = type === "password";
  const [visible, setVisible] = useState(false);

  return (
    <div className={[styles.field, error ? styles.hasError : "", className ?? ""].join(" ")}>
      <label htmlFor={fieldId} className={styles.label}>
        {label}
      </label>
      <div className={styles.inputWrap}>
        {icon && <span className={styles.icon}>{icon}</span>}
        <input
          ref={ref}
          id={fieldId}
          type={isPassword ? (visible ? "text" : "password") : type}
          className={[styles.input, icon ? styles.withIcon : "", isPassword ? styles.withTrailing : ""].join(" ")}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? `${fieldId}-error` : hint ? `${fieldId}-hint` : undefined}
          {...rest}
        />
        {isPassword && (
          <button
            type="button"
            className={styles.trailingBtn}
            onClick={() => setVisible((v) => !v)}
            tabIndex={-1}
            aria-label={visible ? "Ocultar contraseña" : "Mostrar contraseña"}
          >
            {visible ? <EyeOff size={17} /> : <Eye size={17} />}
          </button>
        )}
      </div>
      {error ? (
        <p id={`${fieldId}-error`} className={styles.error} role="alert">
          <AlertCircle size={13} /> {error}
        </p>
      ) : hint ? (
        <p id={`${fieldId}-hint`} className={styles.hint}>
          {hint}
        </p>
      ) : null}
    </div>
  );
});
