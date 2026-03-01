from sqlalchemy import text
from sqlalchemy.engine import Engine


class CatalogosRepository:
    def __init__(self, engine: Engine):
        self.engine = engine

    # =========================
    # PROCESOS / SUBPROCESOS / LÍNEAS
    # =========================

    def listar_procesos(self) -> list[dict]:
        sql = text("""
            SELECT
                id,
                codigo,
                nombre AS nombre_mostrado
            FROM LDA.Procesos
            WHERE activo = 1
            ORDER BY nombre
        """)
        with self.engine.connect() as conn:
            rows = conn.execute(sql).mappings().fetchall()
            return [dict(r) for r in rows]

    def listar_subprocesos(self, id_proceso: int) -> list[dict]:
        sql = text("""
            SELECT
                id,
                codigo,
                nombre AS nombre_mostrado
            FROM LDA.Subprocesos
            WHERE activo = 1
              AND id_proceso = :id_proceso
            ORDER BY nombre
        """)
        with self.engine.connect() as conn:
            rows = conn.execute(sql, {"id_proceso": id_proceso}).mappings().fetchall()
            return [dict(r) for r in rows]

    def listar_lineas_trabajo(self, id_subproceso: int) -> list[dict]:
        sql = text("""
            SELECT
                id,
                codigo,
                nombre AS nombre_mostrado
            FROM LDA.LineasTrabajo
            WHERE activo = 1
              AND id_subproceso = :id_subproceso
            ORDER BY nombre
        """)
        with self.engine.connect() as conn:
            rows = conn.execute(sql, {"id_subproceso": id_subproceso}).mappings().fetchall()
            return [dict(r) for r in rows]

    # =========================
    # CATÁLOGOS EXISTENTES
    # =========================

    def get_modalidades(self) -> list[dict]:
        sql = text("""
            SELECT id, codigo, nombre
            FROM LDA.CatalogoModalidad
            WHERE activo = 1
            ORDER BY orden ASC, id ASC
        """)
        with self.engine.connect() as conn:
            rows = conn.execute(sql).mappings().fetchall()
            return [dict(r) for r in rows]

    def get_tipos_documento(self) -> list[dict]:
        sql = text("""
            SELECT id, codigo, nombre
            FROM LDA.CatalogoTipoDocumento
            WHERE activo = 1
            ORDER BY orden ASC, id ASC
        """)
        with self.engine.connect() as conn:
            rows = conn.execute(sql).mappings().fetchall()
            return [dict(r) for r in rows]

    def get_sedes_by_modalidad_codigo(self, modalidad_codigo: str) -> list[dict]:
        sql = text("""
            SELECT s.id, s.codigo, s.nombre_mostrado, s.es_virtual
            FROM LDA.ModalidadSedePermitida p
            JOIN LDA.CatalogoModalidad m ON m.id = p.id_modalidad
            JOIN LDA.Sedes s ON s.id = p.id_sede
            WHERE m.codigo = :modalidad_codigo
              AND p.permitido = 1
              AND s.activo = 1
            ORDER BY s.orden ASC, s.id ASC
        """)
        with self.engine.connect() as conn:
            rows = conn.execute(sql, {"modalidad_codigo": modalidad_codigo}).mappings().fetchall()
            return [dict(r) for r in rows]
