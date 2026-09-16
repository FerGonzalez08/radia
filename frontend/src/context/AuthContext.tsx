import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import type { RegisterPayload, User } from "../types";
import * as api from "../services/api";
import { shouldRenew } from "../services/jwt";

const SESSION_KEY = "radia.session.v1";
const EXPLICIT_LOGOUT_KEY = "radia.explicit_logout.v1";
const INACTIVITY_LIMIT_MS = 30 * 60 * 1000; // HU006 - Escenario 3
const ACTIVITY_EVENTS = ["mousemove", "keydown", "click", "scroll", "touchstart"] as const;

interface StoredSession {
  accessToken: string;
  refreshToken: string;
}

interface AuthContextValue {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  sessionNotice: string | null;
  clearSessionNotice: () => void;
  register: (payload: RegisterPayload) => Promise<{ correo: string }>;
  verifyEmail: (token: string) => Promise<void>;
  login: (correo: string, password: string) => Promise<User>;
  logout: (notice?: string) => void;
  consumeExplicitLogoutFlag: () => boolean;
  requestPasswordReset: (correo: string) => Promise<{ message: string }>;
  resetPassword: (token: string, password: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function readSession(): StoredSession | null {
  try {
    const raw = localStorage.getItem(SESSION_KEY);
    return raw ? (JSON.parse(raw) as StoredSession) : null;
  } catch {
    return null;
  }
}

function writeSession(session: StoredSession | null) {
  if (session) localStorage.setItem(SESSION_KEY, JSON.stringify(session));
  else localStorage.removeItem(SESSION_KEY);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [refreshToken, setRefreshToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [sessionNotice, setSessionNotice] = useState<string | null>(null);
  const inactivityTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  // Evita condiciones de carrera cuando dos renovaciones se disparan casi
  // al mismo tiempo (el intervalo de refresco y una restauración de sesión).
  const refreshInFlight = useRef<Promise<api.TokenPair> | null>(null);
  // El refresh token rota en cada uso y el backend revoca TODA la sesión
  // si detecta que uno ya usado se reutiliza (protección anti-robo de
  // token). React StrictMode (dev) invoca los efectos dos veces al montar
  // para detectar efectos no idempotentes — sin este guard, esa segunda
  // invocación dispararía un /auth/refresh duplicado con el mismo token
  // y el backend cerraría la sesión que la primera llamada acababa de
  // abrir. El ref persiste entre esa doble invocación (misma instancia
  // de componente), así que garantiza como máximo una llamada real.
  const sessionRestoreStarted = useRef(false);

  const doLogout = useCallback(
    (notice?: string) => {
      if (refreshToken) {
        // Revocación en el backend: best-effort, no bloquea el logout local.
        void api.logoutRemote(refreshToken);
      }
      writeSession(null);
      setUser(null);
      setAccessToken(null);
      setRefreshToken(null);
      if (notice) {
        setSessionNotice(notice);
      } else {
        // Cierre de sesión manual (botón "Cerrar sesión"): a diferencia de
        // HU014 (redirigir a la ruta que se intentaba visitar sin sesión),
        // aquí NO queremos reutilizar esa ruta si luego inicia sesión otra
        // cuenta distinta en el mismo navegador. LoginPage descarta el
        // `from` de la navegación cuando encuentra esta marca.
        try {
          sessionStorage.setItem(EXPLICIT_LOGOUT_KEY, "1");
        } catch {
          // sessionStorage no disponible: no es crítico, se ignora.
        }
      }
    },
    [refreshToken],
  );

  // Restaurar sesión al cargar la app: el access token dura solo 15 min,
  // así que en vez de confiar en el que quedó guardado, se pide uno nuevo
  // de una vez con el refresh token guardado.
  useEffect(() => {
    if (sessionRestoreStarted.current) return;
    sessionRestoreStarted.current = true;
    (async () => {
      const session = readSession();
      if (!session) {
        setIsLoading(false);
        return;
      }
      try {
        const pair = await api.refreshTokenPair(session.refreshToken);
        const restoredUser = await api.fetchMe(pair.accessToken);
        writeSession(pair);
        setAccessToken(pair.accessToken);
        setRefreshToken(pair.refreshToken);
        setUser(restoredUser);
      } catch {
        writeSession(null);
      } finally {
        setIsLoading(false);
      }
    })();
  }, []);

  // HU006 - Escenario 3: cierre de sesión automático tras 30 min de inactividad.
  useEffect(() => {
    if (!accessToken) return;

    const resetTimer = () => {
      if (inactivityTimer.current) clearTimeout(inactivityTimer.current);
      inactivityTimer.current = setTimeout(() => {
        doLogout("Tu sesión se cerró por inactividad. Vuelve a iniciar sesión.");
      }, INACTIVITY_LIMIT_MS);
    };

    ACTIVITY_EVENTS.forEach((evt) => window.addEventListener(evt, resetTimer));
    resetTimer();

    return () => {
      ACTIVITY_EVENTS.forEach((evt) => window.removeEventListener(evt, resetTimer));
      if (inactivityTimer.current) clearTimeout(inactivityTimer.current);
    };
  }, [accessToken, doLogout]);

  // HU004 - Escenario 4: renovación automática del JWT antes de expirar,
  // ahora contra /auth/refresh real (con rotación de refresh token).
  useEffect(() => {
    if (!accessToken || !refreshToken) return;
    const interval = setInterval(async () => {
      if (!shouldRenew(accessToken)) return;
      if (refreshInFlight.current) return;
      const current = refreshToken;
      refreshInFlight.current = api.refreshTokenPair(current);
      try {
        const pair = await refreshInFlight.current;
        writeSession(pair);
        setAccessToken(pair.accessToken);
        setRefreshToken(pair.refreshToken);
      } catch {
        doLogout("Tu sesión expiró. Vuelve a iniciar sesión.");
      } finally {
        refreshInFlight.current = null;
      }
    }, 20_000);
    return () => clearInterval(interval);
  }, [accessToken, refreshToken, doLogout]);

  const login = useCallback(async (correo: string, password: string) => {
    const pair = await api.login(correo, password);
    const loggedInUser = await api.fetchMe(pair.accessToken);
    writeSession(pair);
    setAccessToken(pair.accessToken);
    setRefreshToken(pair.refreshToken);
    setUser(loggedInUser);
    setSessionNotice(null);
    return loggedInUser;
  }, []);

  const consumeExplicitLogoutFlag = useCallback((): boolean => {
    try {
      const wasExplicit = sessionStorage.getItem(EXPLICIT_LOGOUT_KEY) === "1";
      sessionStorage.removeItem(EXPLICIT_LOGOUT_KEY);
      return wasExplicit;
    } catch {
      return false;
    }
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      accessToken,
      isAuthenticated: Boolean(user && accessToken),
      isLoading,
      sessionNotice,
      clearSessionNotice: () => setSessionNotice(null),
      register: api.register,
      verifyEmail: api.verifyEmail,
      login,
      logout: doLogout,
      consumeExplicitLogoutFlag,
      requestPasswordReset: api.requestPasswordReset,
      resetPassword: async (token, password) => {
        await api.resetPassword(token, password);
      },
    }),
    [user, accessToken, isLoading, sessionNotice, login, doLogout, consumeExplicitLogoutFlag],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe usarse dentro de <AuthProvider>");
  return ctx;
}
