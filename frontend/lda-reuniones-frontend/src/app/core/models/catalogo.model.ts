export interface CatalogoItem {
    id: number;
    codigo: string;

    // Para modalidades / tipos documento
    nombre?: string;

    // Para sedes (viene del backend)
    nombre_mostrado?: string;

    // Extra que también viene en sedes
    es_virtual?: boolean;
}
