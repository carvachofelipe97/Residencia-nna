import { Routes, Route, Navigate } from 'react-router-dom';
import { useEffect } from 'react';
import { useAuthStore } from '@/store/authStore';
import Login from '@/pages/Login';
import Dashboard from '@/pages/Dashboard';

// Componente para proteger rutas
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const accessToken = localStorage.getItem('access_token');
  
  if (!isAuthenticated && !accessToken) {
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
};

// Componente para redirigir si ya está autenticado
const PublicRoute = ({ children }: { children: React.ReactNode }) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const accessToken = localStorage.getItem('access_token');
  
  if (isAuthenticated || accessToken) {
    return <Navigate to="/dashboard" replace />;
  }
  
  return <>{children}</>;
};

function App() {
  const initAuth = useAuthStore((state) => state.initAuth);
  
  useEffect(() => {
    initAuth();
  }, [initAuth]);

  return (
    <Routes>
      <Route 
        path="/login" 
        element={
          <PublicRoute>
            <Login />
          </PublicRoute>
        } 
      />
      <Route 
        path="/dashboard" 
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/" 
        element={<Navigate to="/dashboard" replace />} 
      />
      <Route 
        path="*" 
        element={<Navigate to="/dashboard" replace />} 
      />
    </Routes>
  );
}

export default App;
