// Tipos de Alertas

export interface Alerta {
  id: string;
  nna_id?: string;
  usuario_id?: string;
  titulo: string;
  mensaje: string;
  tipo: 
    | "vencimiento_plazo"
    | "audiencia_proxima"
    | "revision_medida"
    | "seguimiento_pendiente"
    | "riesgo_alto"
    | "restriccion_activa"
    | "taller_proximo"
    | "documento_faltante"
    | "intervencion_urgente"
    | "sistema"
    | "otra";
  prioridad: "baja" | "media" | "alta" | "critica";
  fecha_vencimiento?: string;
  fecha_recordatorio?: string;
  estado: "activa" | "en_proceso" | "resuelta" | "descartada";
  entidad_tipo?: string;
  entidad_id?: string;
  url_redirect?: string;
  asignado_a?: string;
  creado_en: string;
  actualizado_en?: string;
  resuelta_en?: string;
  resuelta_por?: string;
  creado_por: string;
  // Campos calculados
  dias_restantes?: number;
}

export interface AlertaCreate {
  nna_id?: string;
  usuario_id?: string;
  titulo: string;
  mensaje: string;
  tipo: string;
  prioridad: "baja" | "media" | "alta" | "critica";
  fecha_vencimiento?: string;
  fecha_recordatorio?: string;
  estado?: "activa" | "en_proceso" | "resuelta" | "descartada";
  entidad_tipo?: string;
  entidad_id?: string;
  url_redirect?: string;
  asignado_a?: string;
}

export interface AlertaUpdate {
  titulo?: string;
  mensaje?: string;
  prioridad?: "baja" | "media" | "alta" | "critica";
  fecha_vencimiento?: string;
  fecha_recordatorio?: string;
  estado?: "activa" | "en_proceso" | "resuelta" | "descartada";
  asignado_a?: string;
}

export interface AlertaStats {
  total: number;
  activas: number;
  criticas: number;
  vencidas: number;
  por_tipo: Record<string, number>;
  por_prioridad: Record<string, number>;
}

// Filtros para alertas
export interface AlertaFiltros {
  nna_id?: string;
  tipo?: string;
  prioridad?: string;
  estado?: string;
  asignado_a?: string;
  solo_activas?: boolean;
  vencidas?: boolean;
}

// Tipos de alerta con labels
export const TIPOS_ALERTA = {
  vencimiento_plazo: "Vencimiento de Plazo",
  audiencia_proxima: "Audiencia Próxima",
  revision_medida: "Revisión de Medida",
  seguimiento_pendiente: "Seguimiento Pendiente",
  riesgo_alto: "Riesgo Alto",
  restriccion_activa: "Restricción Activa",
  taller_proximo: "Taller Próximo",
  documento_faltante: "Documento Faltante",
  intervencion_urgente: "Intervención Urgente",
  sistema: "Sistema",
  otra: "Otra",
} as const;

// Prioridades con colores
export const PRIORIDADES_ALERTA = {
  baja: { label: "Baja", color: "bg-blue-100 text-blue-800 border-blue-200" },
  media: { label: "Media", color: "bg-yellow-100 text-yellow-800 border-yellow-200" },
  alta: { label: "Alta", color: "bg-orange-100 text-orange-800 border-orange-200" },
  critica: { label: "Crítica", color: "bg-red-100 text-red-800 border-red-200" },
} as const;

// Estados con labels
export const ESTADOS_ALERTA = {
  activa: { label: "Activa", color: "bg-red-500" },
  en_proceso: { label: "En Proceso", color: "bg-yellow-500" },
  resuelta: { label: "Resuelta", color: "bg-green-500" },
  descartada: { label: "Descartada", color: "bg-gray-500" },
} as const;
