/**
 * ExportButton — Componente reutilizable de exportación
 * Uso:
 *   <ExportButton
 *     title="Reporte NNA"
 *     fileName="reporte-nna"
 *     columns={[{ key: 'nombre', label: 'Nombre' }, ...]}
 *     data={nnaList}
 *   />
 */
import { useState } from 'react';
import { Download, FileText, FileSpreadsheet, File, ChevronDown, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { exportToExcel, exportToWord, exportToPdf, ExportOptions } from '@/services/exportService';

// ─── TIPOS ────────────────────────────────────────────────────────────────────

export interface ExportButtonProps {
  /** Título del reporte (aparece en el archivo exportado) */
  title: string;
  /** Subtítulo opcional */
  subtitle?: string;
  /** Nombre base del archivo (sin extensión) */
  fileName: string;
  /** Definición de columnas */
  columns: { key: string; label: string; width?: number }[];
  /** Datos a exportar */
  data: Record<string, unknown>[];
  /** Nombre de la organización */
  organization?: string;
  /** Formatos habilitados (por defecto todos) */
  formats?: ('pdf' | 'word' | 'excel')[];
  /** Variante del botón */
  variant?: 'default' | 'outline' | 'ghost';
  /** Tamaño del botón */
  size?: 'sm' | 'default' | 'lg';
  /** Texto del botón (por defecto "Exportar") */
  label?: string;
  /** Clase CSS adicional */
  className?: string;
}

// ─── COMPONENTE ───────────────────────────────────────────────────────────────

export function ExportButton({
  title,
  subtitle,
  fileName,
  columns,
  data,
  organization = 'Residencia NNA',
  formats = ['pdf', 'word', 'excel'],
  variant = 'outline',
  size = 'default',
  label = 'Exportar',
  className = '',
}: ExportButtonProps) {
  const [loading, setLoading] = useState<string | null>(null);

  const options: ExportOptions = { title, subtitle, fileName, columns, data, organization };

  async function handle(format: 'pdf' | 'word' | 'excel') {
    setLoading(format);
    try {
      if (format === 'pdf') exportToPdf(options);
      else if (format === 'excel') await exportToExcel(options);
      else await exportToWord(options);
    } catch (err) {
      console.error('Error al exportar:', err);
      alert('Hubo un error al generar el archivo. Intenta de nuevo.');
    } finally {
      setLoading(null);
    }
  }

  const formatConfig = {
    pdf: {
      label: 'Exportar PDF',
      description: 'Documento para imprimir',
      icon: <FileText className="h-4 w-4 text-red-500" />,
    },
    word: {
      label: 'Exportar Word',
      description: 'Documento editable .docx',
      icon: <File className="h-4 w-4 text-blue-600" />,
    },
    excel: {
      label: 'Exportar Excel',
      description: 'Hoja de cálculo .xlsx',
      icon: <FileSpreadsheet className="h-4 w-4 text-green-600" />,
    },
  };

  const enabledFormats = formats.filter((f) => formatConfig[f]);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant={variant}
          size={size}
          className={`gap-2 ${className}`}
          disabled={loading !== null || data.length === 0}
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Download className="h-4 w-4" />
          )}
          {label}
          <ChevronDown className="h-3 w-3 opacity-60" />
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-52">
        <DropdownMenuLabel className="text-xs text-muted-foreground font-normal">
          {data.length} registro{data.length !== 1 ? 's' : ''} · elegir formato
        </DropdownMenuLabel>
        <DropdownMenuSeparator />

        {enabledFormats.map((format) => {
          const cfg = formatConfig[format];
          return (
            <DropdownMenuItem
              key={format}
              onClick={() => handle(format)}
              disabled={loading !== null}
              className="cursor-pointer gap-3 py-2.5"
            >
              {loading === format ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                cfg.icon
              )}
              <div className="flex flex-col">
                <span className="text-sm font-medium">{cfg.label}</span>
                <span className="text-xs text-muted-foreground">{cfg.description}</span>
              </div>
            </DropdownMenuItem>
          );
        })}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
