// Tipos de Red de Apoyo

export interface Direccion {
  calle?: string;
  numero?: string;
  departamento?: string;
  comuna?: string;
  region?: string;
  codigo_postal?: string;
}

export interface RedApoyo {
  id: string;
  nna_id: string;
  nombre: string;
  apellido: string;
  rut?: string;
  fecha_nacimiento?: string;
  telefono_principal: string;
  telefono_secundario?: string;
  email?: string;
  direccion?: Direccion;
  tipo_vinculo: 
    | "madre" 
    | "padre" 
    | "hermano" 
    | "hermana"
    | "abuela" 
    | "abuelo" 
    | "tia" 
    | "tio"
    | "primo" 
    | "prima" 
    | "padrastro" 
    | "madrastra"
    | "tutor_legal" 
    | "cuidador_temporal"
    | "ppf"
    | "referente_significativo" 
    | "vecino" 
    | "otro";
  descripcion_vinculo?: string;
  es_cuidador_temporal: boolean;
  es_ppf: boolean;
  es_contacto_emergencia: boolean;
  es_referente_significativo: boolean;
  disponibilidad: 
    | "24_horas" 
    | "diurna" 
    | "vespertina" 
    | "fines_semana" 
    | "horario_especifico" 
    | "limitada" 
    | "no_disponible";
  horario_especifico?: string;
  nivel_confiabilidad: "alto" | "medio" | "bajo" | "no_evaluado";
  evaluacion_confiabilidad?: string;
  estado: "activo" | "inactivo" | "pendiente_evaluacion" | "rechazado";
  observaciones?: string;
  tiene_antecedentes?: boolean;
  autorizado_para_retiro: boolean;
  autorizado_para_informacion: boolean;
  fecha_inicio_vinculo?: string;
  fecha_fin_vinculo?: string;
  fecha_ultima_evaluacion?: string;
  evaluado_por?: string;
  creado_en: string;
  actualizado_en?: string;
  creado_por: string;
}

export interface RedApoyoCreate {
  nna_id: string;
  nombre: string;
  apellido: string;
  rut?: string;
  fecha_nacimiento?: string;
  telefono_principal: string;
  telefono_secundario?: string;
  email?: string;
  direccion?: Direccion;
  tipo_vinculo: string;
  descripcion_vinculo?: string;
  es_cuidador_temporal?: boolean;
  es_ppf?: boolean;
  es_contacto_emergencia?: boolean;
  es_referente_significativo?: boolean;
  disponibilidad?: string;
  horario_especifico?: string;
  nivel_confiabilidad?: string;
  evaluacion_confiabilidad?: string;
  estado?: string;
  observaciones?: string;
  tiene_antecedentes?: boolean;
  autorizado_para_retiro?: boolean;
  autorizado_para_informacion?: boolean;
  fecha_inicio_vinculo?: string;
  fecha_fin_vinculo?: string;
}

export interface RedApoyoUpdate {
  nombre?: string;
  apellido?: string;
  rut?: string;
  fecha_nacimiento?: string;
  telefono_principal?: string;
  telefono_secundario?: string;
  email?: string;
  direccion?: Direccion;
  tipo_vinculo?: string;
  descripcion_vinculo?: string;
  es_cuidador_temporal?: boolean;
  es_ppf?: boolean;
  es_contacto_emergencia?: boolean;
  es_referente_significativo?: boolean;
  disponibilidad?: string;
  horario_especifico?: string;
  nivel_confiabilidad?: string;
  evaluacion_confiabilidad?: string;
  estado?: string;
  observaciones?: string;
  tiene_antecedentes?: boolean;
  autorizado_para_retiro?: boolean;
  autorizado_para_informacion?: boolean;
  fecha_inicio_vinculo?: string;
  fecha_fin_vinculo?: string;
}

export interface RedApoyoStats {
  total: number;
  por_tipo_vinculo: Record<string, number>;
  cuidadores_temporales: number;
  ppf: number;
  contactos_emergencia: number;
  por_nivel_confiabilidad: Record<string, number>;
  por_estado: Record<string, number>;
}

// Tipos de vínculo con labels
export const TIPOS_VINCULO = {
  madre: "Madre",
  padre: "Padre",
  hermano: "Hermano",
  hermana: "Hermana",
  abuela: "Abuela",
  abuelo: "Abuelo",
  tia: "Tía",
  tio: "Tío",
  primo: "Primo",
  prima: "Prima",
  padrastro: "Padrastro",
  madrastra: "Madrastra",
  tutor_legal: "Tutor Legal",
  cuidador_temporal: "Cuidador Temporal",
  ppf: "PPF (Protección Familiar)",
  referente_significativo: "Referente Significativo",
  vecino: "Vecino",
  otro: "Otro",
} as const;

// Disponibilidad con labels
export const DISPONIBILIDAD = {
  "24_horas": "24 Horas",
  diurna: "Diurna",
  vespertina: "Vespertina",
  fines_semana: "Fines de Semana",
  horario_especifico: "Horario Específico",
  limitada: "Limitada",
  no_disponible: "No Disponible",
} as const;

// Niveles de confiabilidad con colores
export const NIVELES_CONFIABILIDAD = {
  alto: { label: "Alto", color: "bg-green-100 text-green-800 border-green-200" },
  medio: { label: "Medio", color: "bg-yellow-100 text-yellow-800 border-yellow-200" },
  bajo: { label: "Bajo", color: "bg-red-100 text-red-800 border-red-200" },
  no_evaluado: { label: "No Evaluado", color: "bg-gray-100 text-gray-800 border-gray-200" },
} as const;

// Estados con colores
export const ESTADOS_RED_APOYO = {
  activo: { label: "Activo", color: "bg-green-500" },
  inactivo: { label: "Inactivo", color: "bg-gray-500" },
  pendiente_evaluacion: { label: "Pendiente Evaluación", color: "bg-yellow-500" },
  rechazado: { label: "Rechazado", color: "bg-red-500" },
} as const;
