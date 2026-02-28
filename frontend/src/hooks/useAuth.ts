import { useEffect } from 'react';
import { useAuthStore } from '@/store/authStore';
import { useNavigate } from 'react-router-dom';

export const useAuth = () => {
  const navigate = useNavigate();
  const {
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    logout,
    clearError,
  } = useAuthStore();

  useEffect(() => {
    // Verificar autenticación al montar
    const token = localStorage.getItem('access_token');
    if (!token && isAuthenticated) {
      logout();
    }
  }, []);

  const handleLogin = async (email: string, password: string) => {
    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (error) {
      console.error('Login error:', error);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const hasRole = (roles: string[]) => {
    return user ? roles.includes(user.rol) : false;
  };

  const isAdmin = () => user?.rol === 'admin';
  const isCoordinador = () => user?.rol === 'coordinador' || user?.rol === 'admin';
  const isTecnico = () => user?.rol === 'tecnico' || user?.rol === 'coordinador' || user?.rol === 'admin';

  return {
    user,
    isAuthenticated,
    isLoading,
    error,
    login: handleLogin,
    logout: handleLogout,
    clearError,
    hasRole,
    isAdmin,
    isCoordinador,
    isTecnico,
  };
};
