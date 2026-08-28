const inputClass =
  'w-full rounded border border-outline-variant bg-surface px-gp-sm py-gp-sm text-body-md text-on-surface focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all disabled:opacity-60 disabled:cursor-not-allowed'

export default function Field({ label, htmlFor, children }) {
  return (
    <div className="flex flex-col gap-1 mb-gp-md">
      <label className="text-label-sm text-on-surface-variant uppercase" htmlFor={htmlFor}>
        {label}
      </label>
      {children}
    </div>
  )
}

export function TextInput({ className = '', ...props }) {
  return <input {...props} className={`${inputClass} ${className}`} />
}

export function SelectInput({ className = '', ...props }) {
  return <select {...props} className={`${inputClass} ${className}`} />
}

export function TextareaInput({ className = '', ...props }) {
  return <textarea {...props} className={`${inputClass} ${className}`} />
}
