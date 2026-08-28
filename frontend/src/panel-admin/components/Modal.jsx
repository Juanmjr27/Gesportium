export default function Modal({ title, onClose, children }) {
  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 p-4">
      <div className="bg-surface-container-lowest rounded-xl shadow-xl w-full max-w-[32rem] max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center p-gp-md border-b border-outline-variant sticky top-0 bg-surface-container-lowest">
          <h3 className="text-headline-md text-on-surface">{title}</h3>
          <button
            onClick={onClose}
            className="text-on-surface-variant hover:text-on-surface p-1 rounded-full hover:bg-surface-container-low"
            aria-label="Cerrar"
          >
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>
        <div className="p-gp-md">{children}</div>
      </div>
    </div>
  )
}
