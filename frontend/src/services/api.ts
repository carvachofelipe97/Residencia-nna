import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

// Configuración base de la API
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Crear instancia de axios
const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para agregar token a las peticiones
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Interceptor para manejar errores de respuesta
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    
    // Si el error es 401 y no es el endpoint de login
    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      originalRequest._retry = true;
      
      // Intentar refresh token
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_URL}/api/auth/refresh`, {
            refresh_token: refreshToken,
          });
          
          const { access_token } = response.data;
          localStorage.setItem('access_token', access_token);
          
          // Reintentar la petición original
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${access_token}`;
          }
          return api(originalRequest);
        } catch (refreshError) {
          // Si el refresh falla, logout
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('user');
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      }
    }
    
    return Promise.reject(error);
  }
);

// Servicios de Autenticación
export const authService = {
  login: async (email: string, password: string) => {
    const response = await api.post('/auth/login', { email, password });
    return response.data;
  },
  
  logout: async () => {
    const response = await api.post('/auth/logout');
    return response.data;
  },
  
  getMe: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },
  
  changePassword: async (currentPassword: string, newPassword: string) => {
    const response = await api.post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
    return response.data;
  },
};

// Servicios de Usuarios
export const userService = {
  getAll: async (params?: { skip?: number; limit?: number; rol?: string; activo?: boolean; search?: string }) => {
    const response = await api.get('/usuarios', { params });
    return response.data;
  },
  
  getById: async (id: string) => {
    const response = await api.get(`/usuarios/${id}`);
    return response.data;
  },
  
  create: async (userData: any) => {
    const response = await api.post('/usuarios', userData);
    return response.data;
  },
  
  update: async (id: string, userData: any) => {
    const response = await api.put(`/usuarios/${id}`, userData);
    return response.data;
  },
  
  delete: async (id: string) => {
    const response = await api.delete(`/usuarios/${id}`);
    return response.data;
  },
  
  resetPassword: async (id: string, newPassword: string) => {
    const response = await api.post(`/usuarios/${id}/reset-password`, { new_password: newPassword });
    return response.data;
  },
};

// Servicios de NNA
export const nnaService = {
  getAll: async (params?: { skip?: number; limit?: number; estado?: string; search?: string }) => {
    const response = await api.get('/nna', { params });
    return response.data;
  },
  
  getStats: async () => {
    const response = await api.get('/nna/stats');
    return response.data;
  },
  
  getById: async (id: string) => {
    const response = await api.get(`/nna/${id}`);
    return response.data;
  },
  
  create: async (nnaData: any) => {
    const response = await api.post('/nna', nnaData);
    return response.data;
  },
  
  update: async (id: string, nnaData: any) => {
    const response = await api.put(`/nna/${id}`, nnaData);
    return response.data;
  },
  
  delete: async (id: string) => {
    const response = await api.delete(`/nna/${id}`);
    return response.data;
  },
};

// Servicios de Intervenciones
export const intervencionService = {
  getAll: async (params?: any) => {
    const response = await api.get('/intervenciones', { params });
    return response.data;
  },
  
  getStats: async () => {
    const response = await api.get('/intervenciones/stats');
    return response.data;
  },
  
  getById: async (id: string) => {
    const response = await api.get(`/intervenciones/${id}`);
    return response.data;
  },
  
  create: async (data: any) => {
    const response = await api.post('/intervenciones', data);
    return response.data;
  },
  
  update: async (id: string, data: any) => {
    const response = await api.put(`/intervenciones/${id}`, data);
    return response.data;
  },
  
  delete: async (id: string) => {
    const response = await api.delete(`/intervenciones/${id}`);
    return response.data;
  },
};

// Servicios de Talleres
export const tallerService = {
  getAll: async (params?: any) => {
    const response = await api.get('/talleres', { params });
    return response.data;
  },
  
  getStats: async () => {
    const response = await api.get('/talleres/stats');
    return response.data;
  },
  
  getById: async (id: string) => {
    const response = await api.get(`/talleres/${id}`);
    return response.data;
  },
  
  create: async (data: any) => {
    const response = await api.post('/talleres', data);
    return response.data;
  },
  
  update: async (id: string, data: any) => {
    const response = await api.put(`/talleres/${id}`, data);
    return response.data;
  },
  
  delete: async (id: string) => {
    const response = await api.delete(`/talleres/${id}`);
    return response.data;
  },
  
  addParticipante: async (tallerId: string, participante: any) => {
    const response = await api.post(`/talleres/${tallerId}/participantes`, participante);
    return response.data;
  },
  
  removeParticipante: async (tallerId: string, nnaId: string) => {
    const response = await api.delete(`/talleres/${tallerId}/participantes/${nnaId}`);
    return response.data;
  },
};

// Servicios de Seguimiento
export const seguimientoService = {
  getAll: async (params?: any) => {
    const response = await api.get('/seguimiento', { params });
    return response.data;
  },
  
  getById: async (id: string) => {
    const response = await api.get(`/seguimiento/${id}`);
    return response.data;
  },
  
  create: async (data: any) => {
    const response = await api.post('/seguimiento', data);
    return response.data;
  },
  
  update: async (id: string, data: any) => {
    const response = await api.put(`/seguimiento/${id}`, data);
    return response.data;
  },
  
  delete: async (id: string) => {
    const response = await api.delete(`/seguimiento/${id}`);
    return response.data;
  },
};

// Servicios de Reportes
export const reporteService = {
  getDashboard: async () => {
    const response = await api.get('/reportes/dashboard');
    return response.data;
  },
  
  getNnaReport: async (nnaId: string) => {
    const response = await api.get(`/reportes/nna/detalle/${nnaId}`);
    return response.data;
  },
  
  getIntervencionesPorTipo: async (params?: any) => {
    const response = await api.get('/reportes/intervenciones/por-tipo', { params });
    return response.data;
  },
  
  getTalleresAsistencia: async (params?: any) => {
    const response = await api.get('/reportes/talleres/asistencia', { params });
    return response.data;
  },
  
  getActividadReciente: async (limit?: number) => {
    const response = await api.get('/reportes/actividad/reciente', { params: { limit } });
    return response.data;
  },
};

// Servicios de Alertas
export const alertaService = {
  getAll: async (params?: any) => {
    const response = await api.get('/alertas', { params });
    return response.data;
  },
  
  getStats: async () => {
    const response = await api.get('/alertas/stats');
    return response.data;
  },
  
  getMisAlertas: async () => {
    const response = await api.get('/alertas/mis-alertas');
    return response.data;
  },
  
  getById: async (id: string) => {
    const response = await api.get(`/alertas/${id}`);
    return response.data;
  },
  
  create: async (data: any) => {
    const response = await api.post('/alertas', data);
    return response.data;
  },
  
  update: async (id: string, data: any) => {
    const response = await api.put(`/alertas/${id}`, data);
    return response.data;
  },
  
  resolver: async (id: string, comentario?: string) => {
    const response = await api.post(`/alertas/${id}/resolver`, null, { params: { comentario } });
    return response.data;
  },
  
  asignar: async (id: string, usuarioId: string) => {
    const response = await api.post(`/alertas/${id}/asignar`, null, { params: { usuario_id: usuarioId } });
    return response.data;
  },
  
  delete: async (id: string) => {
    const response = await api.delete(`/alertas/${id}`);
    return response.data;
  },
  
  generarVencimientos: async () => {
    const response = await api.post('/alertas/generar/vencimientos');
    return response.data;
  },
};

// Servicios de Red de Apoyo
export const redApoyoService = {
  getAll: async (params?: any) => {
    const response = await api.get('/red-apoyo', { params });
    return response.data;
  },
  
  getStats: async (nnaId?: string) => {
    const response = await api.get('/red-apoyo/stats', { params: { nna_id: nnaId } });
    return response.data;
  },
  
  getByNna: async (nnaId: string) => {
    const response = await api.get(`/red-apoyo/nna/${nnaId}`);
    return response.data;
  },
  
  getCuidadoresTemporales: async (params?: any) => {
    const response = await api.get('/red-apoyo/cuidadores-temporales', { params });
    return response.data;
  },
  
  getById: async (id: string) => {
    const response = await api.get(`/red-apoyo/${id}`);
    return response.data;
  },
  
  create: async (data: any) => {
    const response = await api.post('/red-apoyo', data);
    return response.data;
  },
  
  update: async (id: string, data: any) => {
    const response = await api.put(`/red-apoyo/${id}`, data);
    return response.data;
  },
  
  evaluar: async (id: string, nivelConfiabilidad: string, evaluacion: string) => {
    const response = await api.post(`/red-apoyo/${id}/evaluar`, null, { 
      params: { nivel_confiabilidad: nivelConfiabilidad, evaluacion } 
    });
    return response.data;
  },
  
  delete: async (id: string) => {
    const response = await api.delete(`/red-apoyo/${id}`);
    return response.data;
  },
};

export default api;
