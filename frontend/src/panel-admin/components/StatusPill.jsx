const VARIANT_CLASSES = {
  success: 'bg-[#D1FAE5] text-[#065F46]',
  warning: 'bg-[#FEF3C7] text-[#92400E]',
  error: 'bg-error-container text-on-error-container',
  neutral: 'bg-surface-variant text-on-surface-variant',
}

export default function StatusPill({ children, variant = 'neutral' }) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium capitalize ${VARIANT_CLASSES[variant] ?? VARIANT_CLASSES.neutral}`}
    >
      {children}
    </span>
  )
}
