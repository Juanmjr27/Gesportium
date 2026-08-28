export default function KpiCard({ label, value, icon, trend }) {
  return (
    <div className="bg-surface-container-lowest border border-outline-variant rounded-lg p-gp-md shadow-sm flex flex-col">
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-label-sm text-outline uppercase tracking-wider">{label}</h3>
        {icon && <span className="material-symbols-outlined text-outline-variant">{icon}</span>}
      </div>
      <div className="flex items-end gap-3 mt-auto">
        <span className="text-headline-xl text-on-surface leading-none">{value}</span>
        {trend && (
          <div
            className={`flex items-center text-sm font-medium px-2 py-0.5 rounded ${
              trend.positive ? 'text-emerald-600 bg-emerald-50' : 'text-on-surface-variant bg-surface-container'
            }`}
          >
            <span className="material-symbols-outlined text-[14px]">
              {trend.positive ? 'trending_up' : 'horizontal_rule'}
            </span>
            {trend.label}
          </div>
        )}
      </div>
    </div>
  )
}
