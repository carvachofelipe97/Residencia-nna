import { useState, useEffect, useCallback } from 'react';
import { reporteService } from '@/services/api';
import { DashboardStats } from '@/types';

export const useDashboard = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await reporteService.getDashboard();
      setStats(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error cargando estadísticas');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  return {
    stats,
    loading,
    error,
    refetch: fetchStats,
  };
};
