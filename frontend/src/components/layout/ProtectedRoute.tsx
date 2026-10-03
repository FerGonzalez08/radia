import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { ROUTE_ROLES } from "../../features/navigation/menuConfig";
import { Spinner } from "../ui/Spinner";

/**
 * HU014 - Bloqueo de rutas no autorizadas.
 * - Sin sesión activa -> redirige a login conservando la ruta de destino
 *   para volver después de autenticarse (Escenario 2 y 3).
 * - Con sesión pero rol no autorizado para la ruta -> redirige a /403
 *   (Escenario 1), sin depender solo de ocultar el botón del menú.
 */
export function ProtectedRoute() {
  const { isAuthenticated, isLoading, user } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="app-shell-loading">
        <Spinner label="Cargando RADIA..." />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/iniciar-sesion" state={{ from: location }} replace />;
  }

  const allowedRoles = ROUTE_ROLES[location.pathname];
  if (allowedRoles && user && !allowedRoles.includes(user.rol)) {
    return <Navigate to="/403" replace />;
  }

  return <Outlet />;
}
