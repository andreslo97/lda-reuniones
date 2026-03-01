from datetime import date
import random
from fastapi import BackgroundTasks

from .repository import ReunionesRepository
from app.utils.emailer import EmailSender
from .schemas import AsistenteIn

import base64
import io
import qrcode


class ReunionesService:
    def __init__(self, repo: ReunionesRepository):
        self.repo = repo

    def _generar_codigo(self, fecha: date) -> str:
        base = fecha.strftime("%Y%m%d")
        for _ in range(20):
            suf = random.randint(100, 999)
            codigo = f"{base}_{suf}"
            if not self.repo.codigo_exists(codigo):
                return codigo
        raise RuntimeError("No se pudo generar un código único para la reunión.")
    
    def _qr_base64_png(self, url: str) -> str:
        qr = qrcode.QRCode(
            version=2,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=6,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    def crear_reunion(self, data, background_tasks: BackgroundTasks) -> dict:
        # Normalizar
        tipo = data.tipo_documento.upper().strip()
        modalidad = data.modalidad.upper().strip()
        sede = data.sede.upper().strip()

        # Validaciones negocio
        if data.fecha < date.today():
            raise ValueError("No se permiten fechas pasadas.")
        if data.hora_fin <= data.hora_inicio:
            raise ValueError("La hora fin debe ser mayor que la hora de inicio.")

        # Validaciones catálogos
        id_tipo = self.repo.get_id_tipo_documento(tipo)
        if not id_tipo:
            raise ValueError("Tipo de documento inválido o inactivo.")

        id_modalidad = self.repo.get_id_modalidad(modalidad)
        if not id_modalidad:
            raise ValueError("Modalidad inválida o inactiva.")

        id_sede = self.repo.get_id_sede(sede)
        if not id_sede:
            raise ValueError("Sede inválida o inactiva.")

        if not self.repo.sede_permitida(id_modalidad, id_sede):
            raise ValueError("La sede seleccionada no está permitida para la modalidad.")

        # ✅ Proceso / Subproceso / Línea (ahora vienen por ID desde el front)
        id_proceso = data.proceso_id
        if not id_proceso:
            raise ValueError("Proceso requerido.")

        # (opcional) validar que exista y esté activo
        if not self.repo.proceso_activo(id_proceso):
            raise ValueError("Proceso inválido o inactivo.")

        id_subproceso = data.subproceso_id
        if id_subproceso is not None:
            if not self.repo.subproceso_activo_y_pertenece(id_subproceso, id_proceso):
                raise ValueError("Subproceso inválido para el proceso seleccionado.")

        id_linea = data.linea_trabajo_id
        if id_linea is not None:
            if not self.repo.linea_activa_y_pertenece(id_linea, id_subproceso):
                raise ValueError("Línea de trabajo inválida para el subproceso seleccionado.")

        # Upsert anfitrión
        anfit = data.anfitrion
        id_anfitrion = self.repo.upsert_anfitrion(
            nombre=anfit.nombre_completo.strip(),
            identificacion=anfit.identificacion.strip(),
            correo=str(anfit.correo).strip(),
            cargo=anfit.cargo.strip(),
        )

        # Generar código y link
        codigo = self._generar_codigo(data.fecha)
        link_registro = f"http://localhost:4200/registro/{codigo}"
        qr_b64 = self._qr_base64_png(link_registro)

        # Insert reunión
        id_reunion = self.repo.insert_reunion(
            codigo=codigo,
            id_tipo_documento=id_tipo,
            nombre_evento=data.nombre.strip(),
            fecha_evento=data.fecha,
            hora_inicio=data.hora_inicio,
            hora_fin=data.hora_fin,
            id_modalidad=id_modalidad,
            id_sede=id_sede,
            lugar_texto=data.lugar_texto.strip(),
            id_anfitrion=id_anfitrion,
            id_proceso=id_proceso,
            id_subproceso=id_subproceso,
            id_linea_trabajo=id_linea,
        )

        # Encolar correo
        asunto = f"Reunión creada: {data.nombre.strip()}"

        html = f"""
        <div style="font-family: Arial, sans-serif; color:#111;">
        <h2 style="margin:0 0 8px;">Reunión creada exitosamente</h2>
        <p style="margin:0 0 16px;">
            Aquí tienes el resumen y el QR para registrar asistentes.
        </p>

        <table style="border-collapse:collapse; width:100%; max-width:640px;">
            <tr>
            <td style="padding:8px; border:1px solid #eee;"><b>Nombre</b></td>
            <td style="padding:8px; border:1px solid #eee;">{data.nombre.strip()}</td>
            </tr>
            <tr>
            <td style="padding:8px; border:1px solid #eee;"><b>Tipo</b></td>
            <td style="padding:8px; border:1px solid #eee;">{tipo}</td>
            </tr>
            <tr>
            <td style="padding:8px; border:1px solid #eee;"><b>Fecha</b></td>
            <td style="padding:8px; border:1px solid #eee;">{data.fecha}</td>
            </tr>
            <tr>
            <td style="padding:8px; border:1px solid #eee;"><b>Hora</b></td>
            <td style="padding:8px; border:1px solid #eee;">{data.hora_inicio} - {data.hora_fin}</td>
            </tr>
            <tr>
            <td style="padding:8px; border:1px solid #eee;"><b>Modalidad</b></td>
            <td style="padding:8px; border:1px solid #eee;">{modalidad}</td>
            </tr>
            <tr>
            <td style="padding:8px; border:1px solid #eee;"><b>Sede</b></td>
            <td style="padding:8px; border:1px solid #eee;">{sede}</td>
            </tr>
            <tr>
            <td style="padding:8px; border:1px solid #eee;"><b>Lugar</b></td>
            <td style="padding:8px; border:1px solid #eee;">{data.lugar_texto.strip()}</td>
            </tr>
            <tr>
            <td style="padding:8px; border:1px solid #eee;"><b>Código</b></td>
            <td style="padding:8px; border:1px solid #eee;"><b>{codigo}</b></td>
            </tr>
            <tr>
            <td style="padding:8px; border:1px solid #eee;"><b>Link de registro</b></td>
            <td style="padding:8px; border:1px solid #eee;">
                <a href="{link_registro}">{link_registro}</a>
            </td>
            </tr>
        </table>

        <hr style="margin:18px 0; border:none; border-top:1px solid #eee;" />

        <h3 style="margin:0 0 8px;">QR de registro</h3>
        <p style="margin:0 0 12px;">Escanéalo para registrar asistentes:</p>

        <img
            src="data:image/png;base64,{qr_b64}"
            alt="QR Registro"
            style="display:block; width:220px; border:1px solid #ddd; border-radius:12px; padding:10px; background:#fff;"
        />
        </div>
        """



        outbox_id = self.repo.enqueue_email(
            id_reunion=id_reunion,
            para=str(anfit.correo),
            asunto=asunto,
            html_body=html,
        )

        # ✅ enviar en background (no bloquea el response del POST)
        background_tasks.add_task(self._send_outbox_email, outbox_id)

        return {"codigo_reunion": codigo, "link_registro": link_registro}

    def _send_outbox_email(self, outbox_id: int) -> None:
        item = self.repo.get_outbox_by_id(outbox_id)
        if not item:
            return

        sender = EmailSender()
        sender.send_html(
            to_email=item["para"],
            subject=item["asunto"],
            html_body=item["html_body"],
        )

    def obtener_reunion(self, codigo: str) -> dict:
        codigo = codigo.strip()
        data = self.repo.get_reunion_by_codigo(codigo)
        if not data:
            raise ValueError("No existe una reunión con ese código.")
        data["link_registro"] = f"http://localhost:4200/registro/{codigo}"
        return data

    def registrar_asistente(self, codigo: str, payload: AsistenteIn, background_tasks: BackgroundTasks):
        id_reunion = self.repo.get_reunion_id_by_codigo(codigo)
        if not id_reunion:
            raise ValueError("No existe una reunión con ese código.")

        # ✅ VALIDACIÓN: solo registrar el MISMO día de la reunión
        fecha_reunion = self.repo.get_reunion_fecha_by_codigo(codigo)  # ya la tienes en el repo
        if not fecha_reunion:
            raise ValueError("No se pudo obtener la fecha de la reunión.")

        if fecha_reunion != date.today():
            raise ValueError("Solo se permite registrar asistentes el mismo día de la reunión.")

        # --- sigue tu lógica normal ---
        id_asistente = self.repo.upsert_asistente(
            nombre=payload.nombre_completo.strip(),
            identificacion=payload.identificacion.strip(),
            correo=str(payload.correo).strip() if payload.correo else None,
            cargo=payload.cargo.strip(),
        )

        if self.repo.reunion_asistente_exists(id_reunion, id_asistente):
            raise RuntimeError("ASISTENTE_YA_REGISTRADO")

        self.repo.link_asistente_a_reunion_full(
            id_reunion=id_reunion,
            id_asistente=id_asistente,
            cargo=payload.cargo.strip(),
            modalidad_asistencia=payload.modalidad_asistencia,
            proceso_id=payload.proceso_id,
            subproceso_id=payload.subproceso_id,
            linea_trabajo_id=payload.linea_trabajo_id,
            institucion_externa=(payload.institucion_externa.strip() if payload.institucion_externa else None),
        )

        # 3) ✅ correo opcional
        email_enviado = False
        if payload.correo:
            reunion = self.repo.get_reunion_by_codigo(codigo)  # trae datos reunión
            asunto = f"Registro de asistencia confirmado - {reunion['nombre_evento']}"
            html = f"""
            <div style="font-family: Arial, sans-serif; color:#111;">
            <h2 style="margin:0 0 8px;">Registro de asistencia confirmado</h2>

            <p style="margin:0 0 14px;">
                Te confirmamos que tu asistencia fue registrada para la siguiente reunión:
            </p>

            <table style="border-collapse:collapse; width:100%; max-width:680px;">
                <tr><td style="padding:8px;border:1px solid #eee;"><b>Código</b></td>
                    <td style="padding:8px;border:1px solid #eee;">{reunion['codigo']}</td></tr>
                <tr><td style="padding:8px;border:1px solid #eee;"><b>Nombre</b></td>
                    <td style="padding:8px;border:1px solid #eee;">{reunion['nombre_evento']}</td></tr>
                <tr><td style="padding:8px;border:1px solid #eee;"><b>Fecha</b></td>
                    <td style="padding:8px;border:1px solid #eee;">{reunion['fecha_evento']}</td></tr>
                <tr><td style="padding:8px;border:1px solid #eee;"><b>Hora</b></td>
                    <td style="padding:8px;border:1px solid #eee;">{reunion['hora_inicio']} - {reunion['hora_fin']}</td></tr>
                <tr><td style="padding:8px;border:1px solid #eee;"><b>Modalidad</b></td>
                    <td style="padding:8px;border:1px solid #eee;">{reunion['modalidad']}</td></tr>
                <tr><td style="padding:8px;border:1px solid #eee;"><b>Sede</b></td>
                    <td style="padding:8px;border:1px solid #eee;">{reunion['sede']}</td></tr>
                <tr><td style="padding:8px;border:1px solid #eee;"><b>Lugar</b></td>
                    <td style="padding:8px;border:1px solid #eee;">{reunion['lugar_texto']}</td></tr>
            </table>

            <hr style="margin:16px 0; border:none; border-top:1px solid #eee;" />

            <h3 style="margin:0 0 8px;">Datos registrados</h3>
            <ul style="margin:0; padding-left:18px;">
                <li><b>Nombre:</b> {payload.nombre_completo}</li>
                <li><b>Identificación:</b> {payload.identificacion}</li>
                <li><b>Cargo:</b> {payload.cargo}</li>
                <li><b>Asistencia:</b> {payload.modalidad_asistencia}</li>
            </ul>
            </div>
            """

            outbox_id = self.repo.enqueue_email(id_reunion, str(payload.correo), asunto, html)

            # ✅ si ya tienes un worker/EmailSender, lo encolas en background
            background_tasks.add_task(self._send_outbox_email, outbox_id)

            email_enviado = True

        return {
            "ok": True,
            "id_reunion": id_reunion,
            "id_asistente": id_asistente,
            "email_enviado": email_enviado,
            "message": "Asistencia registrada correctamente." + (" Revisa tu correo." if email_enviado else ""),
        }

    def listar_asistentes(self, codigo: str) -> dict:
        codigo = codigo.strip()
        id_reunion = self.repo.get_reunion_id_by_codigo(codigo)
        if not id_reunion:
            raise ValueError("No existe una reunión con ese código.")

        asistentes = self.repo.listar_asistentes_por_id_reunion(id_reunion)
        return {"codigo_reunion": codigo, "id_reunion": id_reunion, "asistentes": asistentes}
    