import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import { ProtectedRoute } from "./components/layout/ProtectedRoute";
import { AppLayout } from "./components/layout/AppLayout";
import { Spinner } from "./components/ui/Spinner";

import LandingPage from "./pages/LandingPage";
import LoginPage from "./pages/auth/LoginPage";
import RegisterPage from "./pages/auth/RegisterPage";
import VerifyAccountPage from "./pages/auth/VerifyAccountPage";
import ForgotPasswordPage from "./pages/auth/ForgotPasswordPage";
import ResetPasswordPage from "./pages/auth/ResetPasswordPage";
import DashboardPage from "./pages/DashboardPage";
import ChatPage from "./pages/ChatPage";
import ProfilePage from "./pages/ProfilePage";
import UsersPage from "./pages/UsersPage";
import PermissionsMatrixPage from "./pages/PermissionsMatrixPage";
import ForbiddenPage from "./pages/ForbiddenPage";
import NotFoundPage from "./pages/NotFoundPage";

function Index() {
  const { isAuthenticated, isLoading } = useAuth();
  if (isLoading) {
    return (
      <div className="app-shell-loading">
        <Spinner label="Cargando RADIA..." />
      </div>
    );
  }
  // Con sesión activa, "/" lleva directo al panel; sin sesión, "/" es la
  // pantalla principal pública (landing) en vez de saltar directo al login.
  if (isAuthenticated) {
    return <Navigate to="/app/inicio" replace />;
  }
  return <LandingPage />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Index />} />

      {/* HU001-HU006: autenticación */}
      <Route path="/iniciar-sesion" element={<LoginPage />} />
      <Route path="/registro" element={<RegisterPage />} />
      {/* Rutas de enlace de un solo uso: deben coincidir exactamente con
          las que arma el auth-service real al enviar el correo (ver
          services/auth-service/app/core/email.py del repo de backend). */}
      <Route path="/verify-email" element={<VerifyAccountPage />} />
      <Route path="/recuperar-contrasena" element={<ForgotPasswordPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />

      <Route path="/403" element={<ForbiddenPage />} />

      {/* HU012-HU022: núcleo de la app protegido por sesión + rol */}
      <Route element={<ProtectedRoute />}>
        <Route path="/app" element={<AppLayout />}>
          <Route index element={<Navigate to="inicio" replace />} />
          <Route path="inicio" element={<DashboardPage />} />
          <Route path="chat" element={<ChatPage />} />
          <Route path="perfil" element={<ProfilePage />} />
          <Route path="usuarias" element={<UsersPage />} />
          <Route path="permisos" element={<PermissionsMatrixPage />} />
        </Route>
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
