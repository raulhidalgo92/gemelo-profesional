// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
/** Cálculos del panel «Mi gemelo», separados de la vista para poder probarlos. */

import { CompetenciaGemelo, Experiencia, PerfilCv } from '../../nucleo/gemelo.service';

/** Años distintos trabajados (los periodos solapados cuentan una vez). */
export function aniosExperiencia(experiencias: Experiencia[], hoy: number): number {
  const anios = new Set<number>();
  for (const e of experiencias) {
    if (e.inicio === null) continue;
    const fin = Math.max(e.fin ?? hoy, e.inicio + 1);
    for (let a = e.inicio; a < fin; a++) anios.add(a);
  }
  return anios.size;
}

/** El trabajo actual o, si no hay ninguno abierto, el más reciente. */
export function puestoActual(experiencias: Experiencia[]): Experiencia | undefined {
  return [...experiencias].reverse().find((e) => e.fin === null) ?? experiencias.at(-1);
}

export interface Hito {
  tipo: 'Experiencia' | 'Formación';
  titulo: string;
  fechas: string;
  anio: number;
  actual: boolean;
  /** Posición en la línea de tiempo, en % */
  posicion: number;
}

const SEPARACION_MINIMA = 9;
const POSICION_MAXIMA = 88; // a la derecha queda «Hoy»

/** Hitos de la trayectoria ordenados y colocados en la línea de tiempo sin solaparse. */
export function hitos(perfil: PerfilCv, hoy: number): Hito[] {
  const lista: Omit<Hito, 'posicion'>[] = [
    ...perfil.experiencias.filter(conAnio).map((e) => ({
      tipo: 'Experiencia' as const,
      titulo: e.sector ? `${e.puesto} · ${e.sector}` : e.puesto,
      fechas: fechas(e.inicio, e.fin, 'actualidad'),
      anio: e.inicio!,
      actual: e.fin === null,
    })),
    ...perfil.formacion.filter(conAnio).map((f) => ({
      tipo: 'Formación' as const,
      titulo: f.titulo,
      fechas: fechas(f.inicio, f.fin),
      anio: f.inicio!,
      actual: false,
    })),
  ].sort((a, b) => a.anio - b.anio);
  if (lista.length === 0) return [];

  const desde = lista[0].anio;
  const tramo = Math.max(hoy - desde, 1);
  const posiciones: number[] = [];
  for (const h of lista) {
    const ideal = ((h.anio - desde) / tramo) * POSICION_MAXIMA;
    posiciones.push(Math.max(ideal, (posiciones.at(-1) ?? -SEPARACION_MINIMA) + SEPARACION_MINIMA));
  }
  // Si al separarlos el último se sale, se comprimen todos
  const escala = Math.min(1, POSICION_MAXIMA / Math.max(posiciones.at(-1)!, 1));
  return lista.map((h, i) => ({ ...h, posicion: Math.round(posiciones[i] * escala * 10) / 10 }));
}

function conAnio(e: { inicio: number | null }): boolean {
  return e.inicio !== null;
}

function fechas(inicio: number | null, fin: number | null, abierto?: string): string {
  if (fin === null) return abierto ? `${inicio} – ${abierto}` : `${inicio}`;
  return inicio === fin ? `${inicio}` : `${inicio} – ${fin}`;
}

/** El hito que se muestra al entrar: el trabajo actual o el último. */
export function hitoInicial(lista: Hito[]): number {
  const actual = lista.map((h) => h.actual).lastIndexOf(true);
  return actual >= 0 ? actual : lista.length - 1;
}

const RELATIVO = new Intl.RelativeTimeFormat('es', { numeric: 'auto' });

/** «hoy», «ayer», «hace 3 días», «hace 2 meses»… */
export function haceCuanto(fecha: Date, ahora: Date): string {
  const dias = Math.round((startOfDay(ahora) - startOfDay(fecha)) / 86_400_000);
  if (dias < 30) return RELATIVO.format(-dias, 'day');
  if (dias < 365) return RELATIVO.format(-Math.floor(dias / 30), 'month');
  return RELATIVO.format(-Math.floor(dias / 365), 'year');
}

function startOfDay(d: Date): number {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
}

export const ALCANCES = [
  { clave: 'transversal', titulo: 'Para cualquier trabajo', sub: 'Te acompañan siempre' },
  { clave: 'cross-sector', titulo: 'Entre sectores', sub: 'Útiles en muchos ámbitos' },
  { clave: 'sector-specific', titulo: 'De tu sector', sub: 'Tu especialidad' },
  { clave: 'occupation-specific', titulo: 'De tu puesto', sub: 'Muy específicas' },
];

const MAX_NOMBRES = 4;

export interface ColumnaAlcance {
  titulo: string;
  sub: string;
  total: number;
  demostradas: number;
  /** Las primeras, demostradas antes */
  visibles: CompetenciaGemelo[];
  resto: number;
}

/** Competencias agrupadas por su nivel de reutilización ESCO. */
export function porAlcance(competencias: CompetenciaGemelo[]): ColumnaAlcance[] {
  return ALCANCES.map((a) => {
    const grupo = competencias
      .filter((c) => alcance(c) === a.clave)
      .sort((x, y) => +y.demostrada - +x.demostrada || x.titulo.localeCompare(y.titulo, 'es'));
    return {
      titulo: a.titulo,
      sub: a.sub,
      total: grupo.length,
      demostradas: grupo.filter((c) => c.demostrada).length,
      visibles: grupo.slice(0, MAX_NOMBRES),
      resto: Math.max(grupo.length - MAX_NOMBRES, 0),
    };
  });
}

/** Sin nivel de reutilización conocido, se trata como «entre sectores». */
function alcance(c: CompetenciaGemelo): string {
  return ALCANCES.some((a) => a.clave === c.alcance) ? c.alcance! : 'cross-sector';
}

export interface EstadoGemelo {
  conCv: boolean;
  conDestino: boolean;
  demostradas: number;
  entrevistas: number;
}

export interface Tarea {
  texto: string;
  hecha: boolean;
  ruta: string;
}

export function tareas(e: EstadoGemelo): Tarea[] {
  return [
    { texto: 'Crea tu cuenta', hecha: true, ruta: '/gemelo' },
    { texto: 'Sube tu CV', hecha: e.conCv, ruta: '/bienvenida' },
    { texto: 'Elige tu destino', hecha: e.conDestino, ruta: '/futuro' },
    { texto: 'Demuestra una competencia', hecha: e.demostradas > 0, ruta: '/entrenador' },
    { texto: 'Practica una entrevista', hecha: e.entrevistas > 0, ruta: '/entrenador' },
  ];
}

export type IconoLogro = 'creado' | 'destino' | 'evidencia' | 'entrevista' | 'cinco' | 'meta';

export interface Logro {
  texto: string;
  icono: IconoLogro;
  conseguido: boolean;
}

export function logros(e: EstadoGemelo): Logro[] {
  return [
    { texto: 'Gemelo creado', icono: 'creado', conseguido: e.conCv },
    { texto: 'Con destino', icono: 'destino', conseguido: e.conDestino },
    { texto: 'Primera evidencia', icono: 'evidencia', conseguido: e.demostradas > 0 },
    { texto: 'Primera entrevista', icono: 'entrevista', conseguido: e.entrevistas > 0 },
    { texto: '5 demostradas', icono: 'cinco', conseguido: e.demostradas >= 5 },
    // Llega con la fase del destino: todavía no se puede alcanzar
    { texto: 'Destino alcanzado', icono: 'meta', conseguido: false },
  ];
}
