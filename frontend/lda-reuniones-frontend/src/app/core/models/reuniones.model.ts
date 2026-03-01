export interface ReunionCreateResponse {
    codigo_reunion: string;
    link_registro: string;
}

export interface ReunionDetalle {
    codigo: string;
    tipo_documento: string;
    nombre_evento: string;
    fecha_evento: string;
    hora_inicio: string;
    hora_fin: string;
    modalidad: string;
    sede: string;
    sede_nombre: string;
    lugar_texto: string;
    nombre_completo: string;
    identificacion: string;
    correo: string;
    cargo: string;
    estado: string;
    created_at: string;
    link_registro: string;
}
