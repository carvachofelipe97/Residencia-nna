import { useEffect } from 'react';
import { useRedApoyo } from '@/hooks/useRedApoyo';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Users, 
  Phone, 
  Star,
  ChevronRight,
  Loader2,
  Shield,
  Baby,
  Heart
} from 'lucide-react';
import { 
  TIPOS_VINCULO, 
  NIVELES_CONFIABILIDAD, 
  ESTADOS_RED_APOYO 
} from '@/types/redApoyo';

interface RedApoyoWidgetProps {
  nnaId: string;
  showAll?: boolean;
  limit?: number;
}

export function RedApoyoWidget({ nnaId, showAll = false, limit = 5 }: RedApoyoWidgetProps) {
  const { redApoyo, stats, loading, fetchByNna, fetchStats } = useRedApoyo();

  useEffect(() => {
    if (nnaId) {
      fetchByNna(nnaId);
      fetchStats(nnaId);
    }
  }, [nnaId, fetchByNna, fetchStats]);

  const getConfiabilidadColor = (nivel: string) => {
    return NIVELES_CONFIABILIDAD[nivel as keyof typeof NIVELES_CONFIABILIDAD]?.color || 'bg-gray-100';
  };

  const getTipoVinculoLabel = (tipo: string) => {
    return TIPOS_VINCULO[tipo as keyof typeof TIPOS_VINCULO] || tipo;
  };

  const displayRedApoyo = showAll ? redApoyo : redApoyo.slice(0, limit);

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6 flex items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        </CardContent>
      </Card>
    );
  }

  if (redApoyo.length === 0) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-3 text-gray-500">
            <Users className="h-5 w-5" />
            <span className="text-sm">No hay red de apoyo registrada</span>
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
            <Users className="h-5 w-5" />
            Red de Apoyo
            {redApoyo.length > 0 && (
              <Badge variant="secondary" className="ml-2">
                {redApoyo.length}
              </Badge>
            )}
          </CardTitle>
          {stats && (
            <div className="flex items-center gap-2 text-xs text-gray-500">
              {stats.cuidadores_temporales > 0 && (
                <span className="flex items-center gap-1">
                  <Baby className="h-3 w-3" />
                  {stats.cuidadores_temporales} CT
                </span>
              )}
              {stats.contactos_emergencia > 0 && (
                <span className="flex items-center gap-1">
                  <Phone className="h-3 w-3" />
                  {stats.contactos_emergencia} CE
                </span>
              )}
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {displayRedApoyo.map((miembro) => (
          <div
            key={miembro.id}
            className="p-3 rounded-lg border bg-white hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-medium text-sm">
                    {miembro.nombre} {miembro.apellido}
                  </span>
                  
                  {/* Badges de rol */}
                  <div className="flex items-center gap-1">
                    {miembro.es_contacto_emergencia && (
                      <Badge variant="destructive" className="text-[10px] px-1.5 py-0">
                        <Phone className="h-3 w-3 mr-1" />
                        CE
                      </Badge>
                    )}
                    {miembro.es_cuidador_temporal && (
                      <Badge variant="default" className="text-[10px] px-1.5 py-0 bg-blue-600">
                        <Baby className="h-3 w-3 mr-1" />
                        CT
                      </Badge>
                    )}
                    {miembro.es_ppf && (
                      <Badge variant="default" className="text-[10px] px-1.5 py-0 bg-purple-600">
                        <Shield className="h-3 w-3 mr-1" />
                        PPF
                      </Badge>
                    )}
                  </div>
                </div>
                
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs text-gray-500">
                    {getTipoVinculoLabel(miembro.tipo_vinculo)}
                  </span>
                  <span className="text-gray-300">|</span>
                  <span className={`text-xs px-1.5 py-0.5 rounded border ${getConfiabilidadColor(miembro.nivel_confiabilidad)}`}>
                    {NIVELES_CONFIABILIDAD[miembro.nivel_confiabilidad as keyof typeof NIVELES_CONFIABILIDAD]?.label}
                  </span>
                </div>
                
                <div className="flex items-center gap-3 mt-2 text-xs text-gray-600">
                  <span className="flex items-center gap-1">
                    <Phone className="h-3 w-3" />
                    {miembro.telefono_principal}
                  </span>
                  {miembro.autorizado_para_retiro && (
                    <span className="flex items-center gap-1 text-green-600">
                      <Heart className="h-3 w-3" />
                      Autorizado retiro
                    </span>
                  )}
                </div>
              </div>
              
              <Button
                variant="ghost"
                size="sm"
                className="shrink-0"
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        ))}
        
        {!showAll && redApoyo.length > limit && (
          <Button variant="outline" className="w-full text-sm">
            Ver {redApoyo.length - limit} miembros más
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
