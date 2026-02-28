/**
 * Servicio de Exportación - Residencia NNA
 * Soporta PDF, Word (.docx) y Excel (.xlsx)
 */

// ─── TIPOS ────────────────────────────────────────────────────────────────────

export interface ExportColumn {
  key: string;
  label: string;
  width?: number; // para excel (en caracteres)
}

export interface ExportOptions {
  title: string;
  subtitle?: string;
  fileName: string;
  columns: ExportColumn[];
  data: Record<string, unknown>[];
  /** Nombre de la residencia u organización */
  organization?: string;
}

// ─── HELPERS ─────────────────────────────────────────────────────────────────

function formatDate(): string {
  return new Date().toLocaleDateString('es-CL', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
}

function getCellValue(row: Record<string, unknown>, key: string): string {
  const val = row[key];
  if (val === null || val === undefined) return '—';
  if (val instanceof Date) return val.toLocaleDateString('es-CL');
  return String(val);
}

// ─── EXCEL ────────────────────────────────────────────────────────────────────

/**
 * Exporta datos a un archivo Excel (.xlsx) usando la API nativa de SheetJS
 * Se carga SheetJS dinámicamente desde CDN para no aumentar el bundle.
 */
export async function exportToExcel(options: ExportOptions): Promise<void> {
  const { title, subtitle, fileName, columns, data, organization } = options;

  // Cargar SheetJS dinámicamente
  const XLSX = await loadSheetJS();

  const wb = XLSX.utils.book_new();

  // Filas de cabecera con info del reporte
  const headerRows: string[][] = [
    [organization || 'Residencia NNA', '', '', '', ''],
    [title, '', '', '', ''],
    subtitle ? [subtitle, '', '', '', ''] : [],
    [`Generado: ${formatDate()}`, '', '', '', ''],
    [], // fila vacía
    columns.map((c) => c.label), // encabezados de columna
  ].filter((r) => r.length > 0);

  // Filas de datos
  const dataRows = data.map((row) => columns.map((c) => getCellValue(row, c.key)));

  const allRows = [...headerRows, ...dataRows];
  const ws = XLSX.utils.aoa_to_sheet(allRows);

  // Anchos de columna
  ws['!cols'] = columns.map((c) => ({ wch: c.width || 20 }));

  // Combinar celdas para los títulos (merge primera columna con todo el ancho)
  const colCount = columns.length;
  ws['!merges'] = [
    { s: { r: 0, c: 0 }, e: { r: 0, c: colCount - 1 } },
    { s: { r: 1, c: 0 }, e: { r: 1, c: colCount - 1 } },
  ];
  if (subtitle) {
    ws['!merges'].push({ s: { r: 2, c: 0 }, e: { r: 2, c: colCount - 1 } });
  }

  XLSX.utils.book_append_sheet(wb, ws, 'Reporte');
  XLSX.writeFile(wb, `${fileName}.xlsx`);
}

// ─── WORD ─────────────────────────────────────────────────────────────────────

/**
 * Exporta datos a un archivo Word (.docx) construyendo el XML manualmente.
 * No depende de librerías externas pesadas.
 */
export async function exportToWord(options: ExportOptions): Promise<void> {
  const { title, subtitle, fileName, columns, data, organization } = options;

  // Construir filas de la tabla
  const headerCells = columns
    .map(
      (c) => `
      <w:tc>
        <w:tcPr><w:shd w:val="clear" w:color="auto" w:fill="1e3a5f"/></w:tcPr>
        <w:p><w:pPr><w:jc w:val="center"/></w:pPr>
          <w:r><w:rPr><w:b/><w:color w:val="FFFFFF"/><w:sz w:val="20"/></w:rPr>
            <w:t>${escapeXml(c.label)}</w:t>
          </w:r>
        </w:p>
      </w:tc>`
    )
    .join('');

  const dataRowsXml = data
    .map((row, i) => {
      const fill = i % 2 === 0 ? 'F0F4F8' : 'FFFFFF';
      const cells = columns
        .map(
          (c) => `
          <w:tc>
            <w:tcPr><w:shd w:val="clear" w:color="auto" w:fill="${fill}"/></w:tcPr>
            <w:p><w:r><w:rPr><w:sz w:val="18"/></w:rPr>
              <w:t xml:space="preserve">${escapeXml(getCellValue(row, c.key))}</w:t>
            </w:r></w:p>
          </w:tc>`
        )
        .join('');
      return `<w:tr>${cells}</w:tr>`;
    })
    .join('');

  const docXml = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas"
  xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"
  xmlns:o="urn:schemas-microsoft-com:office:office"
  xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
  xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"
  xmlns:v="urn:schemas-microsoft-com:vml"
  xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing"
  xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
  xmlns:w10="urn:schemas-microsoft-com:office:word"
  xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
  xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml"
  xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup"
  xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk"
  xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml"
  xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape"
  mc:Ignorable="w14 wp14">
  <w:body>
    <!-- Organización -->
    <w:p>
      <w:pPr><w:jc w:val="center"/></w:pPr>
      <w:r><w:rPr><w:b/><w:color w:val="1e3a5f"/><w:sz w:val="28"/></w:rPr>
        <w:t>${escapeXml(organization || 'Residencia NNA')}</w:t>
      </w:r>
    </w:p>
    <!-- Título -->
    <w:p>
      <w:pPr><w:jc w:val="center"/></w:pPr>
      <w:r><w:rPr><w:b/><w:sz w:val="24"/></w:rPr>
        <w:t>${escapeXml(title)}</w:t>
      </w:r>
    </w:p>
    ${
      subtitle
        ? `<w:p>
      <w:pPr><w:jc w:val="center"/></w:pPr>
      <w:r><w:rPr><w:color w:val="666666"/><w:sz w:val="20"/></w:rPr>
        <w:t>${escapeXml(subtitle)}</w:t>
      </w:r>
    </w:p>`
        : ''
    }
    <!-- Fecha -->
    <w:p>
      <w:pPr><w:jc w:val="center"/></w:pPr>
      <w:r><w:rPr><w:color w:val="999999"/><w:sz w:val="18"/></w:rPr>
        <w:t>Generado el ${formatDate()}</w:t>
      </w:r>
    </w:p>
    <!-- Separador -->
    <w:p><w:pPr><w:pBdr><w:bottom w:val="single" w:sz="6" w:space="1" w:color="1e3a5f"/></w:pBdr></w:pPr></w:p>
    <w:p/>
    <!-- Tabla de datos -->
    <w:tbl>
      <w:tblPr>
        <w:tblStyle w:val="TableGrid"/>
        <w:tblW w:w="0" w:type="auto"/>
        <w:tblBorders>
          <w:top w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>
          <w:left w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>
          <w:bottom w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>
          <w:right w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>
          <w:insideH w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>
          <w:insideV w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>
        </w:tblBorders>
        <w:tblCellMar>
          <w:top w:w="100" w:type="dxa"/>
          <w:left w:w="120" w:type="dxa"/>
          <w:bottom w:w="100" w:type="dxa"/>
          <w:right w:w="120" w:type="dxa"/>
        </w:tblCellMar>
      </w:tblPr>
      <w:tblGrid>${columns.map(() => '<w:gridCol w:w="1800"/>').join('')}</w:tblGrid>
      <w:tr>${headerCells}</w:tr>
      ${dataRowsXml}
    </w:tbl>
    <w:p/>
    <!-- Footer -->
    <w:p>
      <w:pPr><w:jc w:val="right"/></w:pPr>
      <w:r><w:rPr><w:color w:val="AAAAAA"/><w:sz w:val="16"/></w:rPr>
        <w:t>Total: ${data.length} registro${data.length !== 1 ? 's' : ''}</w:t>
      </w:r>
    </w:p>
    <w:sectPr>
      <w:pgMar w:top="1000" w:right="1000" w:bottom="1000" w:left="1000"/>
    </w:sectPr>
  </w:body>
</w:document>`;

  const zip = await buildDocxZip(docXml);
  downloadBlob(zip, `${fileName}.docx`, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document');
}

// ─── PDF ──────────────────────────────────────────────────────────────────────

/**
 * Exporta datos a PDF usando la impresión nativa del navegador.
 * No requiere librerías externas; abre una ventana con estilos de impresión optimizados.
 */
export function exportToPdf(options: ExportOptions): void {
  const { title, subtitle, fileName, columns, data, organization } = options;

  const tableRows = data
    .map(
      (row, i) => `
      <tr class="${i % 2 === 0 ? 'even' : ''}">
        ${columns.map((c) => `<td>${escapeHtml(getCellValue(row, c.key))}</td>`).join('')}
      </tr>`
    )
    .join('');

  const html = `<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8"/>
  <title>${escapeHtml(title)}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Inter', sans-serif;
      font-size: 11px;
      color: #1a1a2e;
      background: #fff;
      padding: 24px;
    }
    .header {
      border-bottom: 3px solid #1e3a5f;
      padding-bottom: 16px;
      margin-bottom: 20px;
    }
    .org {
      font-size: 9px;
      font-weight: 600;
      letter-spacing: 0.15em;
      text-transform: uppercase;
      color: #1e3a5f;
    }
    h1 {
      font-size: 20px;
      font-weight: 700;
      color: #1a1a2e;
      margin-top: 4px;
    }
    .subtitle {
      font-size: 12px;
      color: #666;
      margin-top: 2px;
    }
    .meta {
      font-size: 9px;
      color: #aaa;
      margin-top: 6px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 4px;
    }
    thead tr {
      background: #1e3a5f;
      color: #fff;
    }
    thead th {
      padding: 8px 10px;
      text-align: left;
      font-size: 10px;
      font-weight: 600;
      letter-spacing: 0.05em;
    }
    tbody tr td {
      padding: 7px 10px;
      border-bottom: 1px solid #e5e7eb;
      font-size: 10px;
      color: #374151;
    }
    tbody tr.even td { background: #f8fafc; }
    .footer {
      margin-top: 16px;
      display: flex;
      justify-content: space-between;
      font-size: 9px;
      color: #aaa;
    }
    @media print {
      body { padding: 16px; }
      @page { margin: 1cm; size: A4 landscape; }
    }
  </style>
</head>
<body>
  <div class="header">
    <div class="org">${escapeHtml(organization || 'Residencia NNA')}</div>
    <h1>${escapeHtml(title)}</h1>
    ${subtitle ? `<div class="subtitle">${escapeHtml(subtitle)}</div>` : ''}
    <div class="meta">Generado el ${formatDate()}</div>
  </div>
  <table>
    <thead>
      <tr>${columns.map((c) => `<th>${escapeHtml(c.label)}</th>`).join('')}</tr>
    </thead>
    <tbody>${tableRows}</tbody>
  </table>
  <div class="footer">
    <span>${escapeHtml(organization || 'Residencia NNA')} — ${escapeHtml(title)}</span>
    <span>Total: ${data.length} registro${data.length !== 1 ? 's' : ''} · ${formatDate()}</span>
  </div>
  <script>
    window.onload = function() {
      document.title = '${escapeHtml(fileName)}';
      setTimeout(function() { window.print(); }, 300);
    };
  </script>
</body>
</html>`;

  const win = window.open('', '_blank');
  if (!win) {
    alert('Permite las ventanas emergentes para exportar PDF.');
    return;
  }
  win.document.write(html);
  win.document.close();
}

// ─── HELPERS INTERNOS ─────────────────────────────────────────────────────────

function escapeXml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

function escapeHtml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function downloadBlob(data: Uint8Array | ArrayBuffer, fileName: string, mimeType: string): void {
  const blob = new Blob([data], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = fileName;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ─── LOADER DE SHEETJS ────────────────────────────────────────────────────────

let _XLSX: typeof import('xlsx') | null = null;

async function loadSheetJS(): Promise<typeof import('xlsx')> {
  if (_XLSX) return _XLSX;
  // Intentar importación estática primero (si está en package.json)
  try {
    _XLSX = await import('xlsx');
    return _XLSX!;
  } catch {
    // Si no está instalado, cargar desde CDN
    return new Promise((resolve, reject) => {
      if ((window as unknown as Record<string, unknown>).XLSX) {
        _XLSX = (window as unknown as Record<string, unknown>).XLSX as typeof import('xlsx');
        resolve(_XLSX!);
        return;
      }
      const script = document.createElement('script');
      script.src = 'https://cdn.sheetjs.com/xlsx-0.20.3/package/dist/xlsx.full.min.js';
      script.onload = () => {
        _XLSX = (window as unknown as Record<string, unknown>).XLSX as typeof import('xlsx');
        resolve(_XLSX!);
      };
      script.onerror = reject;
      document.head.appendChild(script);
    });
  }
}

// ─── BUILDER DE DOCX (ZIP MANUAL) ────────────────────────────────────────────

async function buildDocxZip(documentXml: string): Promise<Uint8Array> {
  const encoder = new TextEncoder();

  const contentTypes = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>`;

  const rels = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>`;

  const wordRels = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
</Relationships>`;

  const files: Array<{ name: string; data: Uint8Array }> = [
    { name: '[Content_Types].xml', data: encoder.encode(contentTypes) },
    { name: '_rels/.rels', data: encoder.encode(rels) },
    { name: 'word/_rels/document.xml.rels', data: encoder.encode(wordRels) },
    { name: 'word/document.xml', data: encoder.encode(documentXml) },
  ];

  return buildZip(files);
}

// Implementación mínima de ZIP (sin compresión, STORE method)
function buildZip(files: Array<{ name: string; data: Uint8Array }>): Uint8Array {
  const parts: Uint8Array[] = [];
  const centralDir: Uint8Array[] = [];
  let offset = 0;

  for (const file of files) {
    const nameBytes = new TextEncoder().encode(file.name);
    const localHeader = buildLocalFileHeader(nameBytes, file.data);
    parts.push(localHeader);

    const centralEntry = buildCentralDirEntry(nameBytes, file.data, offset);
    centralDir.push(centralEntry);

    offset += localHeader.length + file.data.length;
    parts.push(file.data);
  }

  const centralDirStart = offset;
  let centralDirSize = 0;
  for (const entry of centralDir) {
    parts.push(entry);
    centralDirSize += entry.length;
  }

  const eocd = buildEndOfCentralDir(files.length, centralDirSize, centralDirStart);
  parts.push(eocd);

  const totalSize = parts.reduce((acc, p) => acc + p.length, 0);
  const result = new Uint8Array(totalSize);
  let pos = 0;
  for (const part of parts) {
    result.set(part, pos);
    pos += part.length;
  }
  return result;
}

function buildLocalFileHeader(name: Uint8Array, data: Uint8Array): Uint8Array {
  const crc = crc32(data);
  const header = new ArrayBuffer(30 + name.length);
  const view = new DataView(header);
  view.setUint32(0, 0x04034b50, true); // signature
  view.setUint16(4, 20, true);         // version needed
  view.setUint16(6, 0, true);          // flags
  view.setUint16(8, 0, true);          // compression (STORE)
  view.setUint16(10, 0, true);         // mod time
  view.setUint16(12, 0, true);         // mod date
  view.setUint32(14, crc, true);       // crc32
  view.setUint32(18, data.length, true); // compressed size
  view.setUint32(22, data.length, true); // uncompressed size
  view.setUint16(26, name.length, true); // filename length
  view.setUint16(28, 0, true);           // extra field length
  const arr = new Uint8Array(header);
  arr.set(name, 30);
  return arr;
}

function buildCentralDirEntry(name: Uint8Array, data: Uint8Array, offset: number): Uint8Array {
  const crc = crc32(data);
  const header = new ArrayBuffer(46 + name.length);
  const view = new DataView(header);
  view.setUint32(0, 0x02014b50, true);
  view.setUint16(4, 20, true);
  view.setUint16(6, 20, true);
  view.setUint16(8, 0, true);
  view.setUint16(10, 0, true);
  view.setUint16(12, 0, true);
  view.setUint16(14, 0, true);
  view.setUint32(16, crc, true);
  view.setUint32(20, data.length, true);
  view.setUint32(24, data.length, true);
  view.setUint16(28, name.length, true);
  view.setUint16(30, 0, true);
  view.setUint16(32, 0, true);
  view.setUint16(34, 0, true);
  view.setUint16(36, 0, true);
  view.setUint32(38, 0, true);
  view.setUint32(42, offset, true);
  const arr = new Uint8Array(header);
  arr.set(name, 46);
  return arr;
}

function buildEndOfCentralDir(count: number, size: number, offset: number): Uint8Array {
  const header = new ArrayBuffer(22);
  const view = new DataView(header);
  view.setUint32(0, 0x06054b50, true);
  view.setUint16(4, 0, true);
  view.setUint16(6, 0, true);
  view.setUint16(8, count, true);
  view.setUint16(10, count, true);
  view.setUint32(12, size, true);
  view.setUint32(16, offset, true);
  view.setUint16(20, 0, true);
  return new Uint8Array(header);
}

const CRC_TABLE = (() => {
  const t = new Uint32Array(256);
  for (let i = 0; i < 256; i++) {
    let c = i;
    for (let j = 0; j < 8; j++) {
      c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    }
    t[i] = c;
  }
  return t;
})();

function crc32(data: Uint8Array): number {
  let crc = 0xffffffff;
  for (let i = 0; i < data.length; i++) {
    crc = CRC_TABLE[(crc ^ data[i]) & 0xff] ^ (crc >>> 8);
  }
  return (crc ^ 0xffffffff) >>> 0;
}
