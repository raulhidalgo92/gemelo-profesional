// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, switchMap } from 'rxjs';

export interface CompetenciaGemelo {
  uri: string;
  titulo: string;
  tipo: string | null;
  /** Nivel de reutilización ESCO: transversal, cross-sector, sector-specific u occupation-specific */
  alcance: string | null;
  /** Término del CV del que se dedujo (explicación) */
  origen: string | null;
  /** La añadió el usuario desde el catálogo ESCO */
  anadida: boolean;
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
  /** Nivel de reutilización ESCO */
  alcance: string | null;
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

/** Sin perfil: todavía no hay un CV del que se haya extraído la trayectoria. */
export interface ResumenGemelo {
  perfil: PerfilCv | null;
  actualizado_en: string | null;
}

const TIPOS_CV = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
];
export const MAX_MB_CV = 5;

/** Comprueba el archivo antes de subirlo; devuelve el error o null si vale. */
export function errorDeArchivoCv(archivo: File): string | null {
  if (!TIPOS_CV.includes(archivo.type)) return 'Sube el CV en PDF o en Word (.docx).';
  if (archivo.size > MAX_MB_CV * 1024 * 1024) return `El archivo pesa más de ${MAX_MB_CV} MB.`;
  return null;
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

  resumen(): Observable<ResumenGemelo> {
    return this.http.get<ResumenGemelo>('/api/gemelo');
  }

  competencias(): Observable<CompetenciaGemelo[]> {
    return this.http.get<CompetenciaGemelo[]>('/api/gemelo/competencias');
  }

  /** Añade una competencia del catálogo ESCO que el CV no recogía. */
  anadir(uri: string): Observable<CompetenciaGemelo> {
    return this.http.post<CompetenciaGemelo>('/api/gemelo/competencias', { uri });
  }

  quitar(uri: string): Observable<void> {
    return this.http.delete<void>('/api/gemelo/competencias', { params: { uri } });
  }
}
