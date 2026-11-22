// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

export interface CompetenciaGemelo {
  uri: string;
  titulo: string;
  tipo: string | null;
  /** Término del CV del que se dedujo (explicación) */
  origen: string | null;
  demostrada: boolean;
}

/** Competencias del gemelo del usuario y análisis del CV. */
@Injectable({ providedIn: 'root' })
export class GemeloService {
  private readonly http = inject(HttpClient);

  /** El archivo se analiza en memoria en el servidor y no se guarda. */
  subirCv(archivo: File): Observable<CompetenciaGemelo[]> {
    const datos = new FormData();
    datos.append('archivo', archivo);
    return this.http.post<CompetenciaGemelo[]>('/api/gemelo/cv', datos);
  }

  competencias(): Observable<CompetenciaGemelo[]> {
    return this.http.get<CompetenciaGemelo[]>('/api/gemelo/competencias');
  }

  quitar(uri: string): Observable<void> {
    return this.http.delete<void>('/api/gemelo/competencias', { params: { uri } });
  }
}
