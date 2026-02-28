import { useState, useEffect, useCallback } from 'react';
import { alertaService } from '@/services/api';
import { Alerta, AlertaStats, AlertaCreate, AlertaUpdate } from '@/types/alertas';

interface UseAlertasReturn {
  alertas: Alerta[];
  stats: AlertaStats | null;
  misAlertas: Alerta[];
  loading: boolean;
  error: string | null;
  fetchAlertas: (params?: any) => Promise<void>;
  fetchStats: () => Promise<void>;
  fetchMisAlertas: () => Promise<void>;
  createAlerta: (data: AlertaCreate) => Promise<void>;
  updateAlerta: (id: string, data: AlertaUpdate) => Promise<void>;
  resolverAlerta: (id: string, comentario?: string) => Promise<void>;
  deleteAlerta: (id: string) => Promise<void>;
  generarVencimientos: () => Promise<void>;
}

export const useAlertas = (): UseAlertasReturn => {
  const [alertas, setAlertas] = useState<Alerta[]>([]);
  const [stats, setStats] = useState<AlertaStats | null>(null);
  const [misAlertas, setMisAlertas] = useState<Alerta[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAlertas = useCallback(async (params?: any) => {
    setLoading(true);
    setError(null);
    try {
      const data = await alertaService.getAll(params);
      setAlertas(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error cargando alertas');
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchStats = useCallback(async () => {
    try {
      const data = await alertaService.getStats();
      setStats(data);
    } catch (err: any) {
      console.error('Error cargando estadísticas:', err);
    }
  }, []);

  const fetchMisAlertas = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await alertaService.getMisAlertas();
      setMisAlertas(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error cargando mis alertas');
    } finally {
      setLoading(false);
    }
  }, []);

  const createAlerta = async (data: AlertaCreate) => {
    setLoading(true);
    try {
      await alertaService.create(data);
      await fetchAlertas();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error creando alerta');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const updateAlerta = async (id: string, data: AlertaUpdate) => {
    setLoading(true);
    try {
      await alertaService.update(id, data);
      await fetchAlertas();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error actualizando alerta');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const resolverAlerta = async (id: string, comentario?: string) => {
    setLoading(true);
    try {
      await alertaService.resolver(id, comentario);
      await fetchAlertas();
      await fetchMisAlertas();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error resolviendo alerta');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const deleteAlerta = async (id: string) => {
    setLoading(true);
    try {
      await alertaService.delete(id);
      await fetchAlertas();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error eliminando alerta');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const generarVencimientos = async () => {
    setLoading(true);
    try {
      await alertaService.generarVencimientos();
      await fetchAlertas();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error generando alertas');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    alertas,
    stats,
    misAlertas,
    loading,
    error,
    fetchAlertas,
    fetchStats,
    fetchMisAlertas,
    createAlerta,
    updateAlerta,
    resolverAlerta,
    deleteAlerta,
    generarVencimientos,
  };
};
