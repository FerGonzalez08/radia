import { forwardRef, useId, type ReactNode, type SelectHTMLAttributes } from "react";
import { AlertCircle, ChevronDown } from "lucide-react";
import styles from "./TextField.module.css";
import selectStyles from "./SelectField.module.css";

interface Option {
  value: string;
  label: string;
}

interface SelectFieldProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label: string;
  options: Option[];
  placeholder?: string;
  error?: string | null;
  hint?: ReactNode;
}

export const SelectField = forwardRef<HTMLSelectElement, SelectFieldProps>(function SelectField(
  { label, options, placeholder, error, hint, id, className, ...rest },
  ref,
) {
  const autoId = useId();
  const fieldId = id ?? autoId;

  return (
    <div className={[styles.field, error ? styles.hasError : "", className ?? ""].join(" ")}>
      <label htmlFor={fieldId} className={styles.label}>
        {label}
      </label>
      <div className={selectStyles.wrap}>
        <select id={fieldId} ref={ref} className={[styles.input, selectStyles.select].join(" ")} aria-invalid={Boolean(error)} {...rest}>
          {placeholder && (
            <option value="" disabled hidden>
              {placeholder}
            </option>
          )}
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        <ChevronDown size={16} className={selectStyles.chevron} />
      </div>
      {error ? (
        <p className={styles.error} role="alert">
          <AlertCircle size={13} /> {error}
        </p>
      ) : hint ? (
        <p className={styles.hint}>{hint}</p>
      ) : null}
    </div>
  );
});
