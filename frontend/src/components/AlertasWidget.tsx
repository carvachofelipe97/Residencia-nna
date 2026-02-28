import { useEffect } from 'react';
import { useAlertas } from '@/hooks/useAlertas';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  Bell,
  ChevronRight,
  Loader2
} from 'lucide-react';
import { PRIORIDADES_ALERTA, ESTADOS_ALERTA, TIPOS_ALERTA } from '@/types/alertas';
import { format, parseISO, isPast, differenceInDays } from 'date-fns';
import { es } from 'date-fns/locale';

interface AlertasWidgetProps {
  showAll?: boolean;
  limit?: number;
}

export function AlertasWidget({ showAll = false, limit = 5 }: AlertasWidgetProps) {
  const { misAlertas, loading, fetchMisAlertas, resolverAlerta } = useAlertas();

  useEffect(() => {
    fetchMisAlertas();
  }, [fetchMisAlertas]);

  const handleResolver = async (id: string) => {
    try {
      await resolverAlerta(id);
    } catch (error) {
      console.error('Error resolviendo alerta:', error);
    }
  };

  const getDiasRestantes = (fechaVencimiento?: string) => {
    if (!fechaVencimiento) return null;
    const vencimiento = parseISO(fechaVencimiento);
    const hoy = new Date();
    const dias = differenceInDays(vencimiento, hoy);
    return dias;
  };

  const getPrioridadColor = (prioridad: string) => {
    return PRIORIDADES_ALERTA[prioridad as keyof typeof PRIORIDADES_ALERTA]?.color || 'bg-gray-100';
  };

  const getTipoLabel = (tipo: string) => {
    return TIPOS_ALERTA[tipo as keyof typeof TIPOS_ALERTA] || tipo;
  };

  const displayAlertas = showAll ? misAlertas : misAlertas.slice(0, limit);

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6 flex items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        </CardContent>
      </Card>
    );
  }

  if (misAlertas.length === 0) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-3 text-green-600">
            <CheckCircle className="h-5 w-5" />
            <span className="text-sm">No tienes alertas pendientes</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Bell className="h-5 w-5" />
            Mis Alertas
            {misAlertas.length > 0 && (
              <Badge variant="secondary" className="ml-2">
                {misAlertas.length}
              </Badge>
            )}
          </CardTitle>
          {!showAll && misAlertas.length > limit && (
            <Button variant="ghost" size="sm" className="text-xs">
              Ver todas
              <ChevronRight className="h-4 w-4 ml-1" />
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {displayAlertas.map((alerta) => {
          const diasRestantes = getDiasRestantes(alerta.fecha_vencimiento);
          const estaVencida = diasRestantes !== null && diasRestantes < 0;
          
          return (
            <div
              key={alerta.id}
              className={`p-3 rounded-lg border ${
                alerta.prioridad === 'critica' 
                  ? 'bg-red-50 border-red-200' 
                  : alerta.prioridad === 'alta'
                  ? 'bg-orange-50 border-orange-200'
                  : 'bg-gray-50 border-gray-200'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`text-xs px-2 py-0.5 rounded-full border ${getPrioridadColor(alerta.prioridad)}`}>
                      {PRIORIDADES_ALERTA[alerta.prioridad as keyof typeof PRIORIDADES_ALERTA]?.label}
                    </span>
                    <span className="text-xs text-gray-500">
                      {getTipoLabel(alerta.tipo)}
                    </span>
                  </div>
                  <h4 className="font-medium text-sm mt-1 truncate">{alerta.titulo}</h4>
                  <p className="text-xs text-gray-600 mt-1 line-clamp-2">{alerta.mensaje}</p>
                  
                  {alerta.fecha_vencimiento && (
                    <div className={`flex items-center gap-1 mt-2 text-xs ${
                      estaVencida ? 'text-red-600 font-medium' : 'text-gray-500'
                    }`}>
                      <Clock className="h-3 w-3" />
                      {estaVencida ? (
                        <span>Vencida hace {Math.abs(diasRestantes)} días</span>
                      ) : diasRestantes === 0 ? (
                        <span className="text-orange-600 font-medium">Vence hoy</span>
                      ) : (
                        <span>Vence en {diasRestantes} días</span>
                      )}
                    </div>
                  )}
                </div>
                
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleResolver(alerta.id)}
                  className="shrink-0"
                >
                  <CheckCircle className="h-4 w-4 text-green-600" />
                </Button>
              </div>
            </div>
          );
        })}
        
        {!showAll && misAlertas.length > limit && (
          <Button variant="outline" className="w-full text-sm">
            Ver {misAlertas.length - limit} alertas más
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
