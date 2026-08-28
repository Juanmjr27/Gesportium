import { useEffect, useState } from 'react'
import * as configuracionService from '../services/configuracionService'
import Button from '../components/Button'
import { TextInput } from '../components/Field'

export default function ConfiguracionPage() {
  const [items, setItems] = useState([])
  const [ediciones, setEdiciones] = useState({})
  const [guardandoClave, setGuardandoClave] = useState(null)
  const [error, setError] = useState(null)

  function cargar() {
    configuracionService
      .listarConfiguracion()
      .then(setItems)
      .catch(() => setError('No se pudo cargar la configuración.'))
  }

  useEffect(() => {
    cargar()
  }, [])

  async function handleGuardar(clave) {
    setGuardandoClave(clave)
    try {
      await configuracionService.actualizarConfiguracion(clave, ediciones[clave])
      cargar()
    } catch {
      setError(`No se pudo guardar "${clave}".`)
    } finally {
      setGuardandoClave(null)
    }
  }

  return (
    <div className="flex flex-col gap-gp-lg">
      <div>
        <h1 className="text-headline-xl text-on-background">Configuración general</h1>
        <p className="text-body-lg text-on-surface-variant mt-1">Parámetros globales del sistema.</p>
      </div>

      {error && <p className="text-error">{error}</p>}

      <div className="bg-surface-container-lowest border border-outline-variant rounded-xl divide-y divide-outline-variant">
        {items.length === 0 && <p className="p-gp-md text-on-surface-variant">No hay parámetros configurados.</p>}
        {items.map((item) => {
          const valorActual = ediciones[item.clave] ?? item.valor
          const cambiado = valorActual !== item.valor
          return (
            <div key={item.clave} className="p-gp-md flex items-center gap-gp-md">
              <div className="flex-1">
                <p className="text-body-md font-semibold text-on-surface">{item.clave}</p>
                <p className="text-label-sm text-on-surface-variant">{item.tipo}</p>
              </div>
              <TextInput
                value={valorActual}
                onChange={(e) => setEdiciones({ ...ediciones, [item.clave]: e.target.value })}
                className="w-56"
              />
              <Button
                variant="secondary"
                disabled={!cambiado || guardandoClave === item.clave}
                onClick={() => handleGuardar(item.clave)}
              >
                {guardandoClave === item.clave ? 'Guardando…' : 'Guardar'}
              </Button>
            </div>
          )
        })}
      </div>
    </div>
  )
}
