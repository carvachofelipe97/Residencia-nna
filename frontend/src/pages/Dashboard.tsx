import { useAuth } from '@/hooks/useAuth';
import { useDashboard } from '@/hooks/useDashboard';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  Users, 
  UserCheck, 
  Calendar, 
  AlertTriangle, 
  LogOut, 
  Loader2,
  TrendingUp,
  Activity,
  Bell,
  Users2
} from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { AlertasWidget } from '@/components/AlertasWidget';
import { RedApoyoWidget } from '@/components/RedApoyoWidget';
import { ExportButton } from '@/components/ExportButton';

export default function Dashboard() {
  const { user, logout, isAdmin, isCoordinador } = useAuth();
  const { stats, loading, error, refetch } = useDashboard();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-500 mb-4">{error}</p>
          <Button onClick={refetch}>Reintentar</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-4">
              <h1 className="text-xl font-bold text-gray-900">Residencia NNA</h1>
              <span className="text-sm text-gray-500">|</span>
              <span className="text-sm text-gray-600">Dashboard</span>
            </div>
            <div className="flex items-center gap-3">
              <ExportButton
                title="Resumen del Dashboard"
                subtitle={user?.nombre ? `Generado por: ${user.nombre}` : undefined}
                fileName={`dashboard-${new Date().toISOString().split("T")[0]}`}
                organization="Residencia NNA"
                columns={[
                  { key: "indicador", label: "Indicador", width: 30 },
                  { key: "valor", label: "Valor", width: 15 },
                  { key: "detalle", label: "Detalle", width: 35 },
                ]}
                data={stats ? [
                  { indicador: "Total NNA", valor: stats.nna.total, detalle: `${stats.nna.activos} activos, ${stats.nna.egresados} egresados` },
                  { indicador: "NNA Activos", valor: stats.nna.activos, detalle: "En residencia actualmente" },
                  { indicador: "NNA Egresados", valor: stats.nna.egresados, detalle: "Salida del sistema" },
                  { indicador: "Total Intervenciones", valor: stats.intervenciones.total, detalle: `${stats.intervenciones.pendientes} pendientes` },
                  { indicador: "Intervenciones Urgentes", valor: stats.intervenciones.urgentes, detalle: "Requieren atención inmediata" },
                  { indicador: "Total Talleres", valor: stats.talleres.total, detalle: `${stats.talleres.proximos} próximos este mes` },
                  { indicador: "Usuarios Activos", valor: stats.usuarios.activos, detalle: `Del total de ${stats.usuarios.total}` },
                ] : []}
                size="sm"
                label="Exportar Dashboard"
              />
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900">{user?.nombre}</p>
                <p className="text-xs text-gray-500 capitalize">{user?.rol}</p>
              </div>
              <Button variant="ghost" size="sm" onClick={logout}>
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* NNA Total */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total NNA</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.nna.total || 0}</div>
              <p className="text-xs text-muted-foreground">
                {stats?.nna.activos || 0} activos
              </p>
            </CardContent>
          </Card>

          {/* NNA Activos */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">NNA Activos</CardTitle>
              <UserCheck className="h-4 w-4 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.nna.activos || 0}</div>
              <p className="text-xs text-muted-foreground">
                {stats?.nna.egresados || 0} egresados
              </p>
            </CardContent>
          </Card>

          {/* Intervenciones */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Intervenciones</CardTitle>
              <Activity className="h-4 w-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.intervenciones.total || 0}</div>
              <p className="text-xs text-muted-foreground">
                {stats?.intervenciones.pendientes || 0} pendientes
              </p>
            </CardContent>
          </Card>

          {/* Urgentes */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Urgentes</CardTitle>
              <AlertTriangle className="h-4 w-4 text-red-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">
                {stats?.intervenciones.urgentes || 0}
              </div>
              <p className="text-xs text-muted-foreground">
                Requieren atención
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Intervenciones por Mes */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Intervenciones por Mes
              </CardTitle>
              <CardDescription>
                Últimos 6 meses
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={stats?.intervenciones_por_mes || []}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="mes" 
                      tickFormatter={(value) => {
                        const [year, month] = value.split('-');
                        return `${month}/${year.slice(2)}`;
                      }}
                    />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="cantidad" fill="#3b82f6" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Talleres y Usuarios */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                Resumen del Sistema
              </CardTitle>
              <CardDescription>
                Estadísticas generales
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium">Talleres</p>
                    <p className="text-sm text-gray-500">Total registrados</p>
                  </div>
                  <span className="text-2xl font-bold">{stats?.talleres.total || 0}</span>
                </div>
                
                <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium">Talleres Próximos</p>
                    <p className="text-sm text-gray-500">Este mes</p>
                  </div>
                  <span className="text-2xl font-bold text-green-600">
                    {stats?.talleres.proximos || 0}
                  </span>
                </div>
                
                <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium">Usuarios Activos</p>
                    <p className="text-sm text-gray-500">Del total {stats?.usuarios.total || 0}</p>
                  </div>
                  <span className="text-2xl font-bold">{stats?.usuarios.activos || 0}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        {(isAdmin() || isCoordinador()) && (
          <Card className="mb-8">
            <CardHeader>
              <CardTitle>Acciones Rápidas</CardTitle>
              <CardDescription>
                Accesos directos a funciones frecuentes
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-4">
                <Button variant="outline">
                  <Users className="mr-2 h-4 w-4" />
                  Ver NNA
                </Button>
                <Button variant="outline">
                  <Activity className="mr-2 h-4 w-4" />
                  Nueva Intervención
                </Button>
                <Button variant="outline">
                  <Calendar className="mr-2 h-4 w-4" />
                  Programar Taller
                </Button>
                <Button variant="outline">
                  <Bell className="mr-2 h-4 w-4" />
                  Nueva Alerta
                </Button>
                <Button variant="outline">
                  <Users2 className="mr-2 h-4 w-4" />
                  Red de Apoyo
                </Button>
                {isAdmin() && (
                  <Button variant="outline">
                    <UserCheck className="mr-2 h-4 w-4" />
                    Gestionar Usuarios
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Alertas y Red de Apoyo */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <AlertasWidget limit={5} />
          {/* RedApoyoWidget requiere un nnaId, por ahora mostramos mensaje */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users2 className="h-5 w-5" />
                Red de Apoyo
              </CardTitle>
              <CardDescription>
                Selecciona un NNA para ver su red de apoyo
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-500 text-center py-4">
                Ve a la sección de NNA para ver la red de apoyo de cada caso
              </p>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
