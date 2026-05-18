export default function DataTable({
  columns,
  rows,
  keyField = 'id',
  emptyMessage = 'No data found.',
  rowClassName,
}) {
  if (!rows?.length) {
    return (
      <p className="rounded-xl border border-slate-800 bg-slate-900/50 px-6 py-12 text-center text-sm text-slate-500">
        {emptyMessage}
      </p>
    )
  }

  return (
    <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/50">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[640px] text-left text-sm">
          <thead>
            <tr className="border-b border-slate-800 bg-slate-950/80">
              {columns.map((col) => (
                <th
                  key={col.key}
                  className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500"
                >
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/80">
            {rows.map((row) => (
              <tr
                key={row[keyField]}
                className={`transition-colors hover:bg-slate-800/30 ${
                  typeof rowClassName === 'function' ? rowClassName(row) : rowClassName || ''
                }`}
              >
                {columns.map((col) => (
                  <td key={col.key} className="px-4 py-3 text-slate-300">
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
