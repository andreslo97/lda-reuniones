import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { Observable } from 'rxjs';
import { CatalogoItem } from '../models/catalogo.model';

@Injectable({ providedIn: 'root' })
export class CatalogosService {
  private base = environment.apiUrl;

  constructor(private http: HttpClient) {}

  modalidades(): Observable<CatalogoItem[]> {
    return this.http.get<CatalogoItem[]>(`${this.base}/catalogos/modalidades`);
  }

  sedes(modalidad: string): Observable<CatalogoItem[]> {
    return this.http.get<CatalogoItem[]>(`${this.base}/catalogos/sedes`, {
      params: { modalidad },
    });
  }

  tiposDocumento(): Observable<CatalogoItem[]> {
    return this.http.get<CatalogoItem[]>(`${this.base}/catalogos/tipos-documento`);
  }

  procesos(): Observable<CatalogoItem[]> {
    return this.http.get<CatalogoItem[]>(`${this.base}/catalogos/procesos`);
  }

  // ✅ Subprocesos por id_proceso (NUMÉRICO)
  subprocesos(idProceso: number): Observable<CatalogoItem[]> {
    return this.http.get<CatalogoItem[]>(`${this.base}/catalogos/subprocesos`, {
      params: { id_proceso: String(idProceso) },
    });
  }

  // ✅ Líneas de trabajo por id_subproceso (NUMÉRICO)
  lineasTrabajo(idSubproceso: number): Observable<CatalogoItem[]> {
    return this.http.get<CatalogoItem[]>(`${this.base}/catalogos/lineas-trabajo`, {
      params: { id_subproceso: String(idSubproceso) },
    });
  }
}
