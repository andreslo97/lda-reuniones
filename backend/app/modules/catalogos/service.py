from .repository import CatalogosRepository

class CatalogosService:
    def __init__(self, repo: CatalogosRepository):
        self.repo = repo
    
    def listar_procesos(self):
        return self.repo.listar_procesos()

    def listar_subprocesos(self, id_proceso: int):
        return self.repo.listar_subprocesos(id_proceso)

    def listar_lineas_trabajo(self, id_subproceso: int):
        return self.repo.listar_lineas_trabajo(id_subproceso)

    def modalidades(self):
        return self.repo.get_modalidades()

    def tipos_documento(self):
        return self.repo.get_tipos_documento()

    def sedes_por_modalidad(self, modalidad_codigo: str):
        return self.repo.get_sedes_by_modalidad_codigo(modalidad_codigo.upper())
