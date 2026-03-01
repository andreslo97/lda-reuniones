import traceback
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import Response

from .schemas import (
    ReunionCreateIn,
    ReunionCreateOut,
    AsistenteIn,
    AsistenteOut,
    AsistentesListOut,
    AsistenteRegistroOut,
)
from .service import ReunionesService
from app.utils.qr import make_qr_png_bytes
from app.utils.emailer import EmailSender


def build_router(service: ReunionesService) -> APIRouter:
    router = APIRouter(prefix="/reuniones", tags=["Reuniones"])

    @router.post("", response_model=ReunionCreateOut, status_code=201)
    def crear_reunion(payload: ReunionCreateIn, background_tasks: BackgroundTasks):
        try:
            result = service.crear_reunion(payload, background_tasks)
            return result
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}")

    @router.get("/{codigo}")
    def get_reunion(codigo: str):
        try:
            return service.obtener_reunion(codigo)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}")

    @router.get("/{codigo}/qr")
    def get_qr(codigo: str):
        try:
            data = service.obtener_reunion(codigo)
            png = make_qr_png_bytes(data["link_registro"])
            return Response(content=png, media_type="image/png")
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}")

    @router.post("/{codigo}/asistentes", response_model=AsistenteRegistroOut, status_code=201)
    def registrar_asistente(codigo: str, payload: AsistenteIn, background_tasks: BackgroundTasks):
        try:
            return service.registrar_asistente(codigo, payload, background_tasks)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except RuntimeError as e:
            if str(e) == "ASISTENTE_YA_REGISTRADO":
                raise HTTPException(status_code=409, detail="El asistente ya está registrado en esta reunión.")
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}")

    @router.get("/{codigo}/asistentes", response_model=AsistentesListOut)
    def listar_asistentes(codigo: str):
        try:
            return service.listar_asistentes(codigo)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}")

    return router
