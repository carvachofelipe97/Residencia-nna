import { useState, useEffect, useCallback } from 'react';
import { redApoyoService } from '@/services/api';
import { RedApoyo, RedApoyoStats, RedApoyoCreate, RedApoyoUpdate } from '@/types/redApoyo';

interface UseRedApoyoReturn {
  redApoyo: RedApoyo[];
  stats: RedApoyoStats | null;
  cuidadoresTemporales: RedApoyo[];
  loading: boolean;
  error: string | null;
  fetchRedApoyo: (params?: any) => Promise<void>;
  fetchByNna: (nnaId: string) => Promise<void>;
  fetchStats: (nnaId?: string) => Promise<void>;
  fetchCuidadoresTemporales: (params?: any) => Promise<void>;
  createMiembro: (data: RedApoyoCreate) => Promise<void>;
  updateMiembro: (id: string, data: RedApoyoUpdate) => Promise<void>;
  evaluarMiembro: (id: string, nivelConfiabilidad: string, evaluacion: string) => Promise<void>;
  deleteMiembro: (id: string) => Promise<void>;
}

export const useRedApoyo = (): UseRedApoyoReturn => {
  const [redApoyo, setRedApoyo] = useState<RedApoyo[]>([]);
  const [stats, setStats] = useState<RedApoyoStats | null>(null);
  const [cuidadoresTemporales, setCuidadoresTemporales] = useState<RedApoyo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchRedApoyo = useCallback(async (params?: any) => {
    setLoading(true);
    setError(null);
    try {
      const data = await redApoyoService.getAll(params);
      setRedApoyo(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error cargando red de apoyo');
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchByNna = useCallback(async (nnaId: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await redApoyoService.getByNna(nnaId);
      setRedApoyo(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error cargando red de apoyo del NNA');
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchStats = useCallback(async (nnaId?: string) => {
    try {
      const data = await redApoyoService.getStats(nnaId);
      setStats(data);
    } catch (err: any) {
      console.error('Error cargando estadísticas:', err);
    }
  }, []);

  const fetchCuidadoresTemporales = useCallback(async (params?: any) => {
    setLoading(true);
    setError(null);
    try {
      const data = await redApoyoService.getCuidadoresTemporales(params);
      setCuidadoresTemporales(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error cargando cuidadores temporales');
    } finally {
      setLoading(false);
    }
  }, []);

  const createMiembro = async (data: RedApoyoCreate) => {
    setLoading(true);
    try {
      await redApoyoService.create(data);
      await fetchByNna(data.nna_id);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error creando miembro de red de apoyo');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const updateMiembro = async (id: string, data: RedApoyoUpdate) => {
    setLoading(true);
    try {
      await redApoyoService.update(id, data);
      // Recargar la lista si tenemos un NNA seleccionado
      if (redApoyo.length > 0 && redApoyo[0].nna_id) {
        await fetchByNna(redApoyo[0].nna_id);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error actualizando miembro');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const evaluarMiembro = async (id: string, nivelConfiabilidad: string, evaluacion: string) => {
    setLoading(true);
    try {
      await redApoyoService.evaluar(id, nivelConfiabilidad, evaluacion);
      // Recargar la lista
      if (redApoyo.length > 0 && redApoyo[0].nna_id) {
        await fetchByNna(redApoyo[0].nna_id);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error evaluando miembro');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const deleteMiembro = async (id: string) => {
    setLoading(true);
    try {
      await redApoyoService.delete(id);
      // Recargar la lista
      if (redApoyo.length > 0 && redApoyo[0].nna_id) {
        await fetchByNna(redApoyo[0].nna_id);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error eliminando miembro');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    redApoyo,
    stats,
    cuidadoresTemporales,
    loading,
    error,
    fetchRedApoyo,
    fetchByNna,
    fetchStats,
    fetchCuidadoresTemporales,
    createMiembro,
    updateMiembro,
    evaluarMiembro,
    deleteMiembro,
  };
};
