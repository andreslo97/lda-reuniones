from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.db import engine
from app.modules.catalogos.repository import CatalogosRepository
from app.modules.catalogos.service import CatalogosService
from app.modules.catalogos.router import build_router as build_catalogos_router

from app.modules.reuniones.repository import ReunionesRepository
from app.modules.reuniones.service import ReunionesService
from app.modules.reuniones.router import build_router as build_reuniones_router
from dotenv import load_dotenv

load_dotenv()

# -------------------------------------------------------------------
# App
# -------------------------------------------------------------------
app = FastAPI(
    title="LDA Reuniones API",
    version="0.1.0"
)

# -------------------------------------------------------------------
# CORS (ANGULAR)
# -------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://127.0.0.1:4200",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------
# Catálogos
# -------------------------------------------------------------------
catalogos_repo = CatalogosRepository(engine)
catalogos_service = CatalogosService(catalogos_repo)
app.include_router(build_catalogos_router(catalogos_service))

# -------------------------------------------------------------------
# Reuniones
# -------------------------------------------------------------------
reuniones_repo = ReunionesRepository(engine)
reuniones_service = ReunionesService(reuniones_repo)
app.include_router(build_reuniones_router(reuniones_service))

# -------------------------------------------------------------------
# Healthcheck
# -------------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}
