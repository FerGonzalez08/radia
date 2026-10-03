// Validaciones de formularios de autenticación, alineadas a los criterios
// de aceptación de HU001 (registro), HU002 (verificación) y HU003 (login).

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function isValidEmail(value: string): boolean {
  return EMAIL_RE.test(value.trim());
}

/**
 * HU001 - Escenario 3: "La contraseña debe tener mínimo 8 caracteres alfanuméricos"
 * mínimo 8 caracteres, combinando al menos una letra y un número.
 */
export function getPasswordError(password: string): string | null {
  if (password.length < 8) {
    return "La contraseña debe tener mínimo 8 caracteres alfanuméricos";
  }
  const hasLetter = /[a-zA-Z]/.test(password);
  const hasNumber = /[0-9]/.test(password);
  if (!hasLetter || !hasNumber) {
    return "La contraseña debe tener mínimo 8 caracteres alfanuméricos";
  }
  return null;
}

export function passwordStrength(password: string): { score: number; label: string } {
  let score = 0;
  if (password.length >= 8) score++;
  if (password.length >= 12) score++;
  if (/[A-Z]/.test(password) && /[a-z]/.test(password)) score++;
  if (/[0-9]/.test(password) && /[^a-zA-Z0-9]/.test(password)) score++;
  const labels = ["Muy débil", "Débil", "Aceptable", "Buena", "Excelente"];
  return { score, label: labels[Math.min(score, labels.length - 1)] };
}

export function calculateAge(isoDate: string): number {
  if (!isoDate) return 0;
  const birth = new Date(isoDate);
  if (Number.isNaN(birth.getTime())) return 0;
  const today = new Date();
  let age = today.getFullYear() - birth.getFullYear();
  const monthDiff = today.getMonth() - birth.getMonth();
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
    age--;
  }
  return age;
}

/**
 * HU001 - Escenario 4: bloquear el registro de menores de edad.
 * El criterio original no especificaba el mensaje; se define uno explícito
 * y no ambiguo, en línea con RQNF 4.7 (mensajes de error explícitos).
 */
export function getAgeError(isoDate: string): string | null {
  if (!isoDate) return "Ingresa tu fecha de nacimiento";
  const age = calculateAge(isoDate);
  if (age < 18) {
    return "Debes ser mayor de edad para crear una cuenta en RADIA";
  }
  if (age > 100) {
    return "Verifica la fecha de nacimiento ingresada";
  }
  return null;
}

export function getPhoneError(phone: string): string | null {
  const digits = phone.replace(/\D/g, "");
  if (digits.length < 7 || digits.length > 13) {
    return "Ingresa un número de teléfono válido";
  }
  return null;
}

export function getNameError(name: string): string | null {
  if (name.trim().length < 3) {
    return "Ingresa tu nombre completo";
  }
  return null;
}
