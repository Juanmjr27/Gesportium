from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.modules.accesos.router import router as accesos_router
from app.modules.asistente_ia.router import router as asistente_ia_router
from app.modules.clases.router import router as clases_router
from app.modules.configuracion.router import router as configuracion_router
from app.modules.crm.router import router as crm_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.entrenadores.router import router as entrenadores_router
from app.modules.entrenamiento.router import router as entrenamiento_router
from app.modules.identidad.router import router as identidad_router
from app.modules.informes.router import router as informes_router
from app.modules.membresias.router import router as membresias_router
from app.modules.notificaciones.router import router as notificaciones_router
from app.modules.pagos.router import router as pagos_router
from app.modules.sedes.router import router as sedes_router
from app.modules.socios.router import router as socios_router

app = FastAPI(title="Gesportium API")

# Orígenes del frontend React en desarrollo (Vite y Create React App).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(identidad_router)
app.include_router(sedes_router)
app.include_router(socios_router)
app.include_router(membresias_router)
app.include_router(clases_router)
app.include_router(entrenadores_router)
app.include_router(entrenamiento_router)
app.include_router(pagos_router)
app.include_router(accesos_router)
app.include_router(crm_router)
app.include_router(notificaciones_router)
app.include_router(dashboard_router)
app.include_router(informes_router)
app.include_router(configuracion_router)
app.include_router(asistente_ia_router)
