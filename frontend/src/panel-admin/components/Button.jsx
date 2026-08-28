const VARIANTS = {
  primary: 'bg-primary text-on-primary hover:bg-primary-container shadow-sm',
  secondary: 'border border-outline-variant text-on-surface hover:bg-surface-container-low',
  danger: 'bg-error text-on-error hover:opacity-90',
}

export default function Button({ variant = 'primary', icon, children, className = '', ...props }) {
  return (
    <button
      {...props}
      className={`px-4 py-2 rounded text-button flex items-center gap-2 transition-colors disabled:opacity-60 disabled:cursor-not-allowed ${VARIANTS[variant]} ${className}`}
    >
      {icon && <span className="material-symbols-outlined text-[18px]">{icon}</span>}
      {children}
    </button>
  )
}
