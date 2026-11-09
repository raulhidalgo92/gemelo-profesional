// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

export interface EstadoSalud {
  estado: 'ok' | 'degradado';
  version: string;
  base_datos: boolean;
}

export interface ResumenMercado {
  ocupaciones: number;
  competencias: number;
  transiciones: number;
  ofertas: number;
  ofertas_por_fuente: Record<string, number>;
}

export interface Competencia {
  uri: string;
  titulo: string;
  tipo: string | null;
  similitud: number;
}

/** semantico: por significado (embeddings) · texto: por coincidencia de caracteres */
export type ModoBusqueda = 'semantico' | 'texto';

export interface BusquedaCompetencias {
  modo: ModoBusqueda;
  resultados: Competencia[];
}

/** Acceso a la API REST del backend (siempre bajo /api). */
@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);

  salud(): Observable<EstadoSalud> {
    return this.http.get<EstadoSalud>('/api/salud');
  }

  resumenMercado(): Observable<ResumenMercado> {
    return this.http.get<ResumenMercado>('/api/mercado/resumen');
  }

  buscarCompetencias(q: string, modo: ModoBusqueda): Observable<BusquedaCompetencias> {
    return this.http.get<BusquedaCompetencias>('/api/competencias', { params: { q, modo } });
  }
}
