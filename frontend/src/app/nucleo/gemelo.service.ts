// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, switchMap } from 'rxjs';

export interface CompetenciaGemelo {
  uri: string;
  titulo: string;
  tipo: string | null;
  /** Término del CV del que se dedujo (explicación) */
  origen: string | null;
  demostrada: boolean;
}

export interface Experiencia {
  puesto: string;
  sector: string | null;
  inicio: number | null;
  /** Sin fin: trabajo actual */
  fin: number | null;
}

export interface Formacion {
  titulo: string;
  inicio: number | null;
  fin: number | null;
}

/** Trayectoria extraída del CV, sin empresas ni centros de estudio. */
export interface PerfilCv {
  resumen: string | null;
  experiencias: Experiencia[];
  formacion: Formacion[];
  nivel_ingles: string | null;
}

export interface CompetenciaCv {
  uri: string;
  titulo: string;
  termino: string;
  similitud: number;
  /** No estaba en el gemelo antes de este CV */
  nueva: boolean;
}

/** Cambios que trae un CV, todavía sin guardar. */
export interface AnalisisCv {
  perfil: PerfilCv;
  competencias: CompetenciaCv[];
  /** Solo venían del CV anterior y el nuevo no las trae */
  ya_no: CompetenciaGemelo[];
  trayectoria_cambia: boolean;
}

/** Competencias del gemelo del usuario y análisis del CV. */
@Injectable({ providedIn: 'root' })
export class GemeloService {
  private readonly http = inject(HttpClient);

  /** El archivo se analiza en memoria en el servidor y no se guarda; tampoco el resultado. */
  analizarCv(archivo: File): Observable<AnalisisCv> {
    const datos = new FormData();
    datos.append('archivo', archivo);
    return this.http.post<AnalisisCv>('/api/gemelo/cv/analizar', datos);
  }

  /** Guarda lo que el usuario confirma; `conservar` son URI de `ya_no` que se quedan. */
  aplicarCv(
    perfil: PerfilCv,
    competencias: CompetenciaCv[],
    conservar: string[] = [],
  ): Observable<CompetenciaGemelo[]> {
    return this.http.post<CompetenciaGemelo[]>('/api/gemelo/cv/aplicar', {
      perfil,
      competencias,
      conservar,
    });
  }

  /** Primer CV: no hay nada que revisar, así que se aplica todo lo detectado. */
  subirPrimerCv(archivo: File): Observable<CompetenciaGemelo[]> {
    return this.analizarCv(archivo).pipe(
      switchMap((a) => this.aplicarCv(a.perfil, a.competencias)),
    );
  }

  competencias(): Observable<CompetenciaGemelo[]> {
    return this.http.get<CompetenciaGemelo[]>('/api/gemelo/competencias');
  }

  quitar(uri: string): Observable<void> {
    return this.http.delete<void>('/api/gemelo/competencias', { params: { uri } });
  }
}
