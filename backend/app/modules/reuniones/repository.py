from sqlalchemy import text
from sqlalchemy.engine import Engine
from datetime import date


class ReunionesRepository:
    def __init__(self, engine: Engine):
        self.engine = engine

    # ==============================
    # Catálogos existentes
    # ==============================

    def get_id_tipo_documento(self, codigo: str) -> int | None:
        sql = text("SELECT id FROM LDA.CatalogoTipoDocumento WHERE codigo = :c AND activo = 1")
        with self.engine.connect() as conn:
            row = conn.execute(sql, {"c": codigo}).fetchone()
            return int(row[0]) if row else None

    def get_id_modalidad(self, codigo: str) -> int | None:
        sql = text("SELECT id FROM LDA.CatalogoModalidad WHERE codigo = :c AND activo = 1")
        with self.engine.connect() as conn:
            row = conn.execute(sql, {"c": codigo}).fetchone()
            return int(row[0]) if row else None

    def get_id_sede(self, codigo: str) -> int | None:
        sql = text("SELECT id FROM LDA.Sedes WHERE codigo = :c AND activo = 1")
        with self.engine.connect() as conn:
            row = conn.execute(sql, {"c": codigo}).fetchone()
            return int(row[0]) if row else None

    def sede_permitida(self, id_modalidad: int, id_sede: int) -> bool:
        sql = text("""
            SELECT 1
            FROM LDA.ModalidadSedePermitida
            WHERE id_modalidad = :m AND id_sede = :s AND permitido = 1
        """)
        with self.engine.connect() as conn:
            return conn.execute(sql, {"m": id_modalidad, "s": id_sede}).fetchone() is not None

    # ==============================
    # Anfitrión
    # ==============================

    def upsert_anfitrion(self, nombre: str, identificacion: str, correo: str, cargo: str) -> int:
        sql_select = text("SELECT id FROM LDA.Anfitriones WHERE identificacion = :ident")
        sql_update = text("""
            UPDATE LDA.Anfitriones
            SET nombre_completo = :nombre, correo = :correo, cargo = :cargo
            WHERE identificacion = :ident
        """)
        sql_insert = text("""
            INSERT INTO LDA.Anfitriones (nombre_completo, identificacion, correo, cargo)
            OUTPUT INSERTED.id
            VALUES (:nombre, :ident, :correo, :cargo)
        """)

        with self.engine.begin() as conn:
            row = conn.execute(sql_select, {"ident": identificacion}).fetchone()
            if row:
                conn.execute(
                    sql_update,
                    {"nombre": nombre, "correo": correo, "cargo": cargo, "ident": identificacion},
                )
                return int(row[0])

            new_id = conn.execute(
                sql_insert,
                {"nombre": nombre, "ident": identificacion, "correo": correo, "cargo": cargo},
            ).fetchone()[0]
            return int(new_id)

    # ==============================
    # Reuniones
    # ==============================

    def codigo_exists(self, codigo: str) -> bool:
        sql = text("SELECT 1 FROM LDA.Reuniones WHERE codigo = :c")
        with self.engine.connect() as conn:
            return conn.execute(sql, {"c": codigo}).fetchone() is not None
    
    
    def proceso_activo(self, id_proceso: int) -> bool:
        sql = text("""
            SELECT 1
            FROM LDA.Procesos
            WHERE id = :id
              AND activo = 1
        """)
        with self.engine.connect() as conn:
            return conn.execute(sql, {"id": id_proceso}).first() is not None


    def subproceso_activo_y_pertenece(self, id_subproceso: int, id_proceso: int) -> bool:
        sql = text("""
            SELECT 1
            FROM LDA.Subprocesos
            WHERE id = :id_subproceso
              AND id_proceso = :id_proceso
              AND activo = 1
        """)
        with self.engine.connect() as conn:
            return conn.execute(
                sql,
                {
                    "id_subproceso": id_subproceso,
                    "id_proceso": id_proceso,
                },
            ).first() is not None


    def linea_activa_y_pertenece(self, id_linea: int, id_subproceso: int) -> bool:
        sql = text("""
            SELECT 1
            FROM LDA.LineasTrabajo
            WHERE id = :id_linea
              AND id_subproceso = :id_subproceso
              AND activo = 1
        """)
        with self.engine.connect() as conn:
            return conn.execute(
                sql,
                {
                    "id_linea": id_linea,
                    "id_subproceso": id_subproceso,
                },
            ).first() is not None


    def get_id_proceso(self, valor: str) -> int | None:
        """
        Acepta que el front envíe:
        - codigo (ej: 'GESTION_INFO')
        - o nombre (ej: 'Gestión de la Información')
        """
        sql = text("""
            SELECT TOP 1 id
            FROM LDA.Procesos
            WHERE activo = 1
              AND (
                    LOWER(LTRIM(RTRIM(codigo))) = LOWER(LTRIM(RTRIM(:v)))
                 OR LOWER(LTRIM(RTRIM(nombre))) = LOWER(LTRIM(RTRIM(:v)))
              )
        """)
        with self.engine.connect() as conn:
            row = conn.execute(sql, {"v": valor}).fetchone()
            return int(row[0]) if row else None

    def get_id_subproceso(self, valor: str, id_proceso: int) -> int | None:
        """
        Acepta codigo o nombre del subproceso, pero SIEMPRE amarrado al proceso.
        """
        sql = text("""
            SELECT TOP 1 id
            FROM LDA.Subprocesos
            WHERE activo = 1
              AND id_proceso = :id_proceso
              AND (
                    LOWER(LTRIM(RTRIM(codigo))) = LOWER(LTRIM(RTRIM(:v)))
                 OR LOWER(LTRIM(RTRIM(nombre))) = LOWER(LTRIM(RTRIM(:v)))
              )
        """)
        with self.engine.connect() as conn:
            row = conn.execute(sql, {"v": valor, "id_proceso": id_proceso}).fetchone()
            return int(row[0]) if row else None

    def get_id_linea_trabajo(self, valor: str, id_subproceso: int | None) -> int | None:
        """
        Acepta codigo o nombre de la línea, pero SIEMPRE amarrada al subproceso.
        """
        if not id_subproceso:
            return None

        sql = text("""
            SELECT TOP 1 id
            FROM LDA.LineasTrabajo
            WHERE activo = 1
              AND id_subproceso = :id_subproceso
              AND (
                    LOWER(LTRIM(RTRIM(codigo))) = LOWER(LTRIM(RTRIM(:v)))
                 OR LOWER(LTRIM(RTRIM(nombre))) = LOWER(LTRIM(RTRIM(:v)))
              )
        """)
        with self.engine.connect() as conn:
            row = conn.execute(sql, {"v": valor, "id_subproceso": id_subproceso}).fetchone()
            return int(row[0]) if row else None

    # ==============================
    # ✅ INSERT reunión con ids proceso/subproceso/linea
    # ==============================

    def insert_reunion(
        self,
        codigo: str,
        id_tipo_documento: int,
        nombre_evento: str,
        fecha_evento,
        hora_inicio,
        hora_fin,
        id_modalidad: int,
        id_sede: int,
        lugar_texto: str,
        id_anfitrion: int,
        id_proceso: int | None = None,
        id_subproceso: int | None = None,
        id_linea_trabajo: int | None = None,
    ) -> int:
        sql = text("""
            INSERT INTO LDA.Reuniones
            (codigo, id_tipo_documento, nombre_evento, fecha_evento, hora_inicio, hora_fin,
             id_modalidad, id_sede, lugar_texto, id_anfitrion, estado,
             id_proceso, id_subproceso, id_linea_trabajo)
            OUTPUT INSERTED.id
            VALUES
            (:codigo, :id_tipo, :nombre, :fecha, :h_ini, :h_fin,
             :id_mod, :id_sede, :lugar, :id_anfit, 'CREADA',
             :id_proceso, :id_subproceso, :id_linea_trabajo)
        """)
        with self.engine.begin() as conn:
            row = conn.execute(
                sql,
                {
                    "codigo": codigo,
                    "id_tipo": id_tipo_documento,
                    "nombre": nombre_evento,
                    "fecha": fecha_evento,
                    "h_ini": hora_inicio,
                    "h_fin": hora_fin,
                    "id_mod": id_modalidad,
                    "id_sede": id_sede,
                    "lugar": lugar_texto,
                    "id_anfit": id_anfitrion,
                    "id_proceso": id_proceso,
                    "id_subproceso": id_subproceso,
                    "id_linea_trabajo": id_linea_trabajo,
                },
            ).fetchone()
            return int(row[0])

    def enqueue_email(self, id_reunion: int, para: str, asunto: str, html_body: str) -> None:
        sql = text("""
            INSERT INTO LDA.CorreoOutbox (id_reunion, para, asunto, html_body)
            VALUES (:id_reunion, :para, :asunto, :html)
        """)
        with self.engine.begin() as conn:
            conn.execute(sql, {"id_reunion": id_reunion, "para": para, "asunto": asunto, "html": html_body})

    def get_reunion_by_codigo(self, codigo: str) -> dict | None:
        sql = text("""
            SELECT
                r.codigo,
                td.codigo AS tipo_documento,
                r.nombre_evento,
                r.fecha_evento,
                r.hora_inicio,
                r.hora_fin,
                m.codigo AS modalidad,
                s.codigo AS sede,
                s.nombre_mostrado AS sede_nombre,
                r.lugar_texto,
                a.nombre_completo,
                a.identificacion,
                a.correo,
                a.cargo,
                r.estado,
                r.created_at,
                r.id_proceso,
                r.id_subproceso,
                r.id_linea_trabajo
            FROM LDA.Reuniones r
            JOIN LDA.CatalogoTipoDocumento td ON td.id = r.id_tipo_documento
            JOIN LDA.CatalogoModalidad m ON m.id = r.id_modalidad
            JOIN LDA.Sedes s ON s.id = r.id_sede
            JOIN LDA.Anfitriones a ON a.id = r.id_anfitrion
            WHERE r.codigo = :codigo
        """)
        with self.engine.connect() as conn:
            row = conn.execute(sql, {"codigo": codigo}).mappings().fetchone()
            return dict(row) if row else None

    def get_reunion_id_by_codigo(self, codigo: str) -> int | None:
        sql = text("SELECT id FROM LDA.Reuniones WHERE codigo = :c")
        with self.engine.connect() as conn:
            row = conn.execute(sql, {"c": codigo}).fetchone()
            return int(row[0]) if row else None
        
    def get_reunion_fecha_by_codigo(self, codigo: str) -> date | None:
        sql = text("""
            SELECT fecha_evento
            FROM LDA.Reuniones
            WHERE codigo = :codigo
        """)
        with self.engine.connect() as conn:
            row = conn.execute(sql, {"codigo": codigo}).fetchone()
            return row[0] if row else None

    # ==============================
    # Asistentes (lo que ya tenías)
    # ==============================

    def listar_asistentes_por_id_reunion(self, id_reunion: int) -> list[dict]:
        sql = text("""
            SELECT
                a.id,
                a.nombre_completo,
                a.identificacion,
                a.correo,

                ra.cargo,
                ra.modalidad_asistencia,

                ra.proceso_id,
                p.nombre AS proceso,

                ra.subproceso_id,
                sp.nombre AS subproceso,

                ra.linea_trabajo_id,
                lt.nombre AS linea_trabajo,

                ra.created_at
            FROM LDA.ReunionAsistentes ra
            JOIN LDA.Asistentes a ON a.id = ra.id_asistente

            LEFT JOIN LDA.Procesos p ON p.id = ra.proceso_id
            LEFT JOIN LDA.Subprocesos sp ON sp.id = ra.subproceso_id
            LEFT JOIN LDA.LineasTrabajo lt ON lt.id = ra.linea_trabajo_id

            WHERE ra.id_reunion = :id_reunion
            ORDER BY ra.created_at DESC
        """)
        with self.engine.connect() as conn:
            rows = conn.execute(sql, {"id_reunion": id_reunion}).mappings().fetchall()
            return [dict(r) for r in rows]
        
    def upsert_asistente(self, nombre: str, identificacion: str, correo: str | None, cargo: str) -> int:
        sql_select = text("SELECT id FROM LDA.Asistentes WHERE identificacion = :ident")

        sql_update = text("""
            UPDATE LDA.Asistentes
            SET nombre_completo = :nombre,
                correo = :correo,
                cargo = :cargo
            WHERE identificacion = :ident
        """)

        sql_insert = text("""
            INSERT INTO LDA.Asistentes (nombre_completo, identificacion, correo, cargo)
            OUTPUT INSERTED.id
            VALUES (:nombre, :ident, :correo, :cargo)
        """)

        with self.engine.begin() as conn:
            row = conn.execute(sql_select, {"ident": identificacion}).fetchone()
            if row:
                conn.execute(sql_update, {
                    "nombre": nombre,
                    "correo": correo,
                    "cargo": cargo,
                    "ident": identificacion
                })
                return int(row[0])

            new_id = conn.execute(sql_insert, {
                "nombre": nombre,
                "ident": identificacion,
                "correo": correo,
                "cargo": cargo
            }).fetchone()[0]
            return int(new_id)


    def reunion_asistente_exists(self, id_reunion: int, id_asistente: int) -> bool:
        sql = text("""
            SELECT 1
            FROM LDA.ReunionAsistentes
            WHERE id_reunion = :r AND id_asistente = :a
        """)
        with self.engine.connect() as conn:
            return conn.execute(sql, {"r": id_reunion, "a": id_asistente}).fetchone() is not None

    def link_asistente_a_reunion(
        self,
        id_reunion: int,
        id_asistente: int,
        cargo: str | None,
        modalidad_asistencia: str,
        proceso_id: int | None,
        subproceso_id: int | None,
        linea_trabajo_id: int | None,
    ) -> None:
        """
        Inserta en LDA.ReunionAsistentes incluyendo los nuevos campos.
        """
        sql = text("""
            INSERT INTO LDA.ReunionAsistentes
                (id_reunion, id_asistente, cargo, modalidad_asistencia, proceso_id, subproceso_id, linea_trabajo_id)
            VALUES
                (:r, :a, :cargo, :modalidad, :pid, :spid, :ltid)
        """)
        with self.engine.begin() as conn:
            conn.execute(
                sql,
                {
                    "r": id_reunion,
                    "a": id_asistente,
                    "cargo": cargo,
                    "modalidad": modalidad_asistencia,
                    "pid": proceso_id,
                    "spid": subproceso_id,
                    "ltid": linea_trabajo_id,
                },
            )

    def list_asistentes_by_reunion(self, id_reunion: int) -> list[dict]:
        sql = text("""
            SELECT
                a.id,
                a.nombre_completo,
                a.identificacion,
                a.correo,
                ra.created_at
            FROM LDA.ReunionAsistentes ra
            JOIN LDA.Asistentes a ON a.id = ra.id_asistente
            WHERE ra.id_reunion = :r
            ORDER BY ra.created_at DESC
        """)
        with self.engine.connect() as conn:
            rows = conn.execute(sql, {"r": id_reunion}).mappings().fetchall()
            return [dict(r) for r in rows]
        
    def get_outbox_by_id(self, outbox_id: int) -> dict | None:
        sql = text("""
            SELECT id, para, asunto, html_body
            FROM LDA.CorreoOutbox
            WHERE id = :id
        """)
        with self.engine.connect() as conn:
            row = conn.execute(sql, {"id": outbox_id}).mappings().fetchone()
            return dict(row) if row else None

    def enqueue_email(self, id_reunion: int, para: str, asunto: str, html_body: str) -> int:
        sql = text("""
            INSERT INTO LDA.CorreoOutbox (id_reunion, para, asunto, html_body)
            OUTPUT INSERTED.id
            VALUES (:id_reunion, :para, :asunto, :html)
        """)
        with self.engine.begin() as conn:
            row = conn.execute(sql, {"id_reunion": id_reunion, "para": para, "asunto": asunto, "html": html_body}).fetchone()
            return int(row[0])
        
    def link_asistente_a_reunion_full(
        self,
        id_reunion: int,
        id_asistente: int,
        cargo: str,
        modalidad_asistencia: str,
        proceso_id: int | None,
        subproceso_id: int | None,
        linea_trabajo_id: int | None,
        institucion_externa: str | None,
    ) -> None:
        sql = text("""
            INSERT INTO LDA.ReunionAsistentes
            (
                id_reunion,
                id_asistente,
                cargo,
                modalidad_asistencia,
                proceso_id,
                subproceso_id,
                linea_trabajo_id,
                institucion_externa
            )
            VALUES
            (
                :id_reunion,
                :id_asistente,
                :cargo,
                :modalidad_asistencia,
                :proceso_id,
                :subproceso_id,
                :linea_trabajo_id,
                :institucion_externa
            )
        """)
        with self.engine.begin() as conn:
            conn.execute(sql, {
                "id_reunion": id_reunion,
                "id_asistente": id_asistente,
                "cargo": cargo,
                "modalidad_asistencia": modalidad_asistencia,
                "proceso_id": proceso_id,
                "subproceso_id": subproceso_id,
                "linea_trabajo_id": linea_trabajo_id,
                "institucion_externa": institucion_externa,
            })

