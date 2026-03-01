from __future__ import annotations

from datetime import date, time, datetime
from typing import List, Optional
import re

from pydantic import BaseModel, Field, EmailStr
from typing_extensions import Literal


# =========================
# Regex reutilizables
# =========================
NOMBRE_REGEX = r"^[A-Za-zÁÉÍÓÚáéíóúÑñÜü\s]+$"
ID_REGEX = r"^\d+$"


# =========================
# Inputs (Crear Reunión)
# =========================
class AnfitrionIn(BaseModel):
    nombre_completo: str = Field(min_length=3, max_length=200, pattern=NOMBRE_REGEX)
    identificacion: str = Field(min_length=6, max_length=20, pattern=ID_REGEX)
    correo: EmailStr
    cargo: str = Field(min_length=2, max_length=150)


class ReunionCreateIn(BaseModel):
    tipo_documento: str  # ASISTENCIA | DESPLIEGUE
    nombre: str = Field(min_length=3, max_length=300)

    fecha: date
    hora_inicio: time
    hora_fin: time

    modalidad: str  # PRESENCIAL | VIRTUAL | HIBRIDA
    sede: str       # código sede (PRINCIPAL, AMB_PRADO, etc.)
    lugar_texto: str = Field(min_length=2, max_length=250)

    anfitrion: AnfitrionIn

    # ✅ Clasificación (guardada como FK en Reuniones)
    proceso_id: int
    subproceso_id: Optional[int] = None
    linea_trabajo_id: Optional[int] = None


class ReunionCreateOut(BaseModel):
    codigo_reunion: str
    link_registro: str


# =========================
# Inputs (Registro Asistentes)
# =========================
class AsistenteIn(BaseModel):
    nombre_completo: str = Field(min_length=3, max_length=200)
    identificacion: str = Field(min_length=6, max_length=30, pattern=ID_REGEX)

    # ✅ correo opcional y si viene debe ser válido
    correo: Optional[EmailStr] = None

    cargo: str = Field(min_length=2, max_length=150)
    modalidad_asistencia: str  # PRESENCIAL | VIRTUAL

    proceso_id: Optional[int] = None
    subproceso_id: Optional[int] = None
    linea_trabajo_id: Optional[int] = None
    
    institucion_externa: Optional[str] = Field(default=None, max_length=200)


class AsistenteOut(BaseModel):
    id: int
    nombre_completo: str
    identificacion: str
    # ✅ puede venir null
    correo: Optional[str] = None

    cargo: Optional[str] = None
    modalidad_asistencia: Optional[str] = None

    created_at: datetime
    proceso_id: Optional[int] = None
    subproceso_id: Optional[int] = None
    linea_trabajo_id: Optional[int] = None

    proceso_nombre: Optional[str] = None
    subproceso_nombre: Optional[str] = None
    linea_trabajo_nombre: Optional[str] = None


class AsistentesListOut(BaseModel):
    codigo_reunion: str
    id_reunion: int
    asistentes: List[AsistenteOut]


class AsistenteRegistroOut(BaseModel):
    ok: bool
    id_reunion: int
    id_asistente: int
    # ✅ indica si se mandó correo
    email_enviado: bool
    message: str
