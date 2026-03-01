from fastapi import APIRouter, Query, HTTPException
from .service import CatalogosService

def build_router(service: CatalogosService) -> APIRouter:
    router = APIRouter(prefix="/catalogos", tags=["Catálogos"])

    @router.get("/modalidades")
    def modalidades():
        return service.modalidades()

    @router.get("/procesos")
    def listar_procesos():
        return service.listar_procesos()

    @router.get("/subprocesos")
    def listar_subprocesos(id_proceso: int = Query(...)):
        return service.listar_subprocesos(id_proceso)

    @router.get("/lineas-trabajo")
    def listar_lineas_trabajo(id_subproceso: int = Query(...)):
        return service.listar_lineas_trabajo(id_subproceso)

    @router.get("/tipos-documento")
    def tipos_documento():
        return service.tipos_documento()

    @router.get("/sedes")
    def sedes(modalidad: str = Query(..., min_length=3, description="PRESENCIAL | VIRTUAL | HIBRIDA")):
        data = service.sedes_por_modalidad(modalidad)
        if not data:
            raise HTTPException(status_code=404, detail="No hay sedes para la modalidad enviada.")
        return data

    return router
