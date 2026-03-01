import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { Observable } from 'rxjs';
import { ReunionCreateResponse, ReunionDetalle } from '../models/reuniones.model';

@Injectable({ providedIn: 'root' })
export class ReunionesService {
    private base = environment.apiUrl;

    constructor(private http: HttpClient) {}

    crear(payload: any): Observable<ReunionCreateResponse> {
    return this.http.post<ReunionCreateResponse>(`${this.base}/reuniones`, payload);
    }

    detalle(codigo: string): Observable<ReunionDetalle> {
    return this.http.get<ReunionDetalle>(`${this.base}/reuniones/${codigo}`);
    }

    qrUrl(codigo: string): string {
    return `${this.base}/reuniones/${codigo}/qr`;
    }

    registrarAsistente(codigo: string, payload: any) {
        return this.http.post(`${this.base}/reuniones/${codigo}/asistentes`, payload);
    }

    listarAsistentes(codigo: string) {
        return this.http.get(`${this.base}/reuniones/${codigo}/asistentes`);
    }

    obtenerReunion(codigo: string): Observable<any> {
        return this.http.get<any>(`${this.base}/reuniones/${codigo}`);
    }
}
