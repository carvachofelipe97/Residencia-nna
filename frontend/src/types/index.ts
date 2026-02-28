// Tipos de Usuario
export interface User {
  id: string;
  email: string;
  nombre: string;
  rol: 'admin' | 'tecnico' | 'coordinador' | 'viewer';
  activo: boolean;
  ultimo_acceso?: string;
  creado_en: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

// Tipos de NNA
export interface NNA {
  id: string;
  nombre: string;
  apellido: string;
  rut?: string;
  fecha_nacimiento?: string;
  edad?: number;
  genero: string;
  fecha_ingreso: string;
  fecha_egreso?: string;
  estado: 'activo' | 'egresado' | 'trasladado' | 'temporal';
  telefono?: string;
  direccion?: string;
  comuna?: string;
  region?: string;
  contacto_emergencia?: {
    nombre?: string;
    telefono?: string;
    relacion?: string;
  };
  alergias?: string;
  medicamentos?: string;
  condiciones_medicas?: string;
  establecimiento_educacional?: string;
  curso?: string;
  observaciones?: string;
  creado_en: string;
  actualizado_en?: string;
}

// Tipos de Intervención
export interface Intervencion {
  id: string;
  nna_id: string;
  fecha: string;
  tipo: string;
  motivo: string;
  descripcion: string;
  resultados?: string;
  derivacion?: string;
  estado: 'pendiente' | 'en_proceso' | 'completada' | 'cancelada';
  prioridad: 'baja' | 'media' | 'alta' | 'urgente';
  fecha_proximo_seguimiento?: string;
  creado_en: string;
  creado_por: string;
}

// Tipos de Taller
export interface Taller {
  id: string;
  nombre: string;
  descripcion?: string;
  fecha: string;
  hora_inicio: string;
  hora_termino: string;
  ubicacion?: string;
  objetivos?: string;
  materiales?: string;
  responsable_id: string;
  participantes: ParticipanteTaller[];
  capacidad_maxima: number;
  estado: string;
  creado_en: string;
}

export interface ParticipanteTaller {
  nna_id: string;
  asistencia: boolean;
  evaluacion?: string;
  observaciones?: string;
}

// Tipos de Seguimiento
export interface Seguimiento {
  id: string;
  nna_id: string;
  fecha: string;
  tipo: string;
  area_salud?: string;
  area_educativa?: string;
  area_social?: string;
  area_familiar?: string;
  area_emocional?: string;
  evaluacion_general: string;
  fortalezas?: string;
  dificultades?: string;
  objetivos_corto_plazo?: string;
  objetivos_medio_plazo?: string;
  objetivos_largo_plazo?: string;
  recomendaciones?: string;
  estado: string;
  creado_en: string;
  creado_por: string;
}

// Dashboard Stats
export interface DashboardStats {
  nna: {
    total: number;
    activos: number;
    egresados: number;
  };
  intervenciones: {
    total: number;
    pendientes: number;
    urgentes: number;
  };
  talleres: {
    total: number;
    proximos: number;
  };
  usuarios: {
    total: number;
    activos: number;
  };
  intervenciones_por_mes: {
    mes: string;
    cantidad: number;
  }[];
}

// Notificación
export interface Notificacion {
  id: string;
  titulo: string;
  mensaje: string;
  tipo: string;
  prioridad: string;
  leida: boolean;
  creado_en: string;
}
