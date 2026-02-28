# 📤 Módulo de Exportación — Residencia NNA

## Archivos agregados

```
frontend/src/
├── services/
│   └── exportService.ts      ← Lógica de exportación (PDF, Word, Excel)
└── components/
    └── ExportButton.tsx       ← Componente de botón reutilizable
```

---

## Instalación

Agrega `xlsx` al proyecto para la exportación Excel:

```bash
cd frontend
npm install xlsx
```

> Si no instalas `xlsx`, el sistema lo cargará automáticamente desde CDN la primera vez que se use Excel.

---

## Uso del componente

```tsx
import { ExportButton } from '@/components/ExportButton';

// En cualquier página o componente:
<ExportButton
  title="Listado de NNA"
  subtitle="Período: Enero - Diciembre 2025"
  fileName="nna-2025"
  organization="Residencia NNA"
  columns={[
    { key: 'nombre', label: 'Nombre completo', width: 30 },
    { key: 'rut', label: 'RUT', width: 15 },
    { key: 'edad', label: 'Edad', width: 10 },
    { key: 'estado', label: 'Estado', width: 15 },
    { key: 'fecha_ingreso', label: 'Fecha Ingreso', width: 20 },
  ]}
  data={listaNNA}  // array de objetos
  formats={['pdf', 'word', 'excel']}  // puedes limitar los formatos
/>
```

---

## Props del componente

| Prop           | Tipo                          | Default         | Descripción                          |
|----------------|-------------------------------|-----------------|--------------------------------------|
| `title`        | `string`                      | requerido       | Título del reporte                   |
| `subtitle`     | `string`                      | —               | Subtítulo opcional                   |
| `fileName`     | `string`                      | requerido       | Nombre del archivo sin extensión     |
| `columns`      | `ExportColumn[]`              | requerido       | Definición de columnas               |
| `data`         | `Record<string, unknown>[]`   | requerido       | Datos a exportar                     |
| `organization` | `string`                      | `'Residencia NNA'` | Nombre de la organización         |
| `formats`      | `('pdf'\|'word'\|'excel')[]`  | todos           | Formatos habilitados                 |
| `variant`      | `'default'\|'outline'\|'ghost'` | `'outline'`   | Estilo del botón                     |
| `size`         | `'sm'\|'default'\|'lg'`       | `'default'`     | Tamaño del botón                     |
| `label`        | `string`                      | `'Exportar'`    | Texto del botón                      |

---

## Ejemplos por módulo

### Exportar NNA

```tsx
<ExportButton
  title="Listado de NNA"
  fileName="nna"
  columns={[
    { key: 'nombre', label: 'Nombre', width: 30 },
    { key: 'rut', label: 'RUT', width: 14 },
    { key: 'edad', label: 'Edad', width: 8 },
    { key: 'estado', label: 'Estado', width: 15 },
  ]}
  data={nnaList}
/>
```

### Exportar Intervenciones

```tsx
<ExportButton
  title="Intervenciones"
  subtitle="Filtradas por período"
  fileName="intervenciones"
  columns={[
    { key: 'nna_nombre', label: 'NNA', width: 25 },
    { key: 'tipo', label: 'Tipo', width: 20 },
    { key: 'prioridad', label: 'Prioridad', width: 15 },
    { key: 'estado', label: 'Estado', width: 15 },
    { key: 'fecha', label: 'Fecha', width: 15 },
  ]}
  data={intervenciones}
  formats={['pdf', 'excel']}  // Sin Word para este caso
/>
```

### Exportar Talleres

```tsx
<ExportButton
  title="Talleres Programados"
  fileName="talleres"
  columns={[
    { key: 'nombre', label: 'Taller', width: 25 },
    { key: 'facilitador', label: 'Facilitador', width: 20 },
    { key: 'fecha', label: 'Fecha', width: 15 },
    { key: 'participantes', label: 'Participantes', width: 15 },
  ]}
  data={talleres}
/>
```

---

## Cómo funciona cada formato

### 📄 PDF
- Abre una ventana nueva del navegador con el reporte formateado
- El usuario usa **Ctrl+P / Cmd+P** o el diálogo de impresión del navegador
- Optimizado para **A4 horizontal**
- No requiere librerías externas

### 📝 Word (.docx)
- Genera un archivo `.docx` nativo con tabla formateada
- No requiere librerías externas (ZIP construido manualmente)
- Compatible con Microsoft Word, LibreOffice, Google Docs

### 📊 Excel (.xlsx)
- Usa la librería **SheetJS** (cargada desde CDN si no está instalada)
- Incluye encabezados, títulos y celdas combinadas
- Compatible con Microsoft Excel, LibreOffice Calc, Google Sheets
