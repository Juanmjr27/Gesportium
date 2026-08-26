import uuid

from sqlalchemy.orm import Session

from app.modules.configuracion.models import ConfiguracionGlobal, HistorialConfiguracion

VALORES_BOOLEANO = ("true", "false")


def validar_valor(tipo: str, valor: str) -> None:
    if tipo == "numero":
        try:
            float(valor)
        except ValueError:
            raise ValueError(f"El valor '{valor}' no es un número válido")
    elif tipo == "booleano" and valor not in VALORES_BOOLEANO:
        raise ValueError(f"El valor '{valor}' no es un booleano válido (use 'true' o 'false')")


def editar_configuracion(
    db: Session, config: ConfiguracionGlobal, valor_nuevo: str, autor_id: uuid.UUID
) -> ConfiguracionGlobal:
    validar_valor(config.tipo, valor_nuevo)

    historial = HistorialConfiguracion(
        clave=config.clave,
        valor_anterior=config.valor,
        valor_nuevo=valor_nuevo,
        autor_id=autor_id,
    )
    db.add(historial)

    config.valor = valor_nuevo
    db.commit()
    db.refresh(config)
    return config
