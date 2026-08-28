// Tabla genérica de solo lectura: columns = [{ key, label, render?, align? }]
export default function DataTable({ columns, rows, rowKey, emptyMessage = 'Sin resultados.', onRowClick }) {
  return (
    <div className="bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-surface-container-low border-b border-outline-variant">
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={`py-gp-sm px-gp-md text-label-sm text-on-surface-variant uppercase tracking-wider ${col.align === 'right' ? 'text-right' : ''}`}
                >
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="text-body-md divide-y divide-outline-variant/50">
            {rows.length === 0 && (
              <tr>
                <td className="py-gp-lg px-gp-md text-center text-on-surface-variant" colSpan={columns.length}>
                  {emptyMessage}
                </td>
              </tr>
            )}
            {rows.map((row) => (
              <tr
                key={row[rowKey]}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
                className={`hover:bg-surface-container-highest/30 transition-colors ${onRowClick ? 'cursor-pointer' : ''}`}
              >
                {columns.map((col) => (
                  <td
                    key={col.key}
                    className={`py-gp-sm px-gp-md text-on-surface ${col.align === 'right' ? 'text-right' : ''}`}
                  >
                    {col.render ? col.render(row) : row[col.key]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
