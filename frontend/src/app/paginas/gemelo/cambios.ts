// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
/** Qué cambia en el gemelo con un CV nuevo, para revisarlo antes de aplicarlo. */

import { PerfilCv } from '../../nucleo/gemelo.service';
import { normalizar } from './panel';

export interface CambioTrayectoria {
  tipo: 'nueva' | 'editada' | 'quitada';
  titulo: string;
  detalle: string;
  /** Es un puesto de trabajo (para contar las experiencias nuevas) */
  experiencia?: boolean;
}

interface Tramo {
  clave: string;
  titulo: string;
  fechas: string;
  nueva: string;
  experiencia: boolean;
}

/** Compara la trayectoria guardada con la del CV nuevo. */
export function cambiosTrayectoria(antes: PerfilCv | null, despues: PerfilCv): CambioTrayectoria[] {
  const cambios: CambioTrayectoria[] = [];
  const previos = new Map(tramos(antes).map((t) => [t.clave, t]));
  const nuevos = tramos(despues);

  for (const t of nuevos) {
    const previo = previos.get(t.clave);
    if (!previo) {
      const detalle = unir(t.fechas, t.nueva);
      cambios.push({ tipo: 'nueva', titulo: t.titulo, detalle, experiencia: t.experiencia });
    } else if (previo.fechas !== t.fechas) {
      cambios.push({ tipo: 'editada', titulo: t.titulo, detalle: `Ahora ${t.fechas}` });
    }
  }
  const claves = new Set(nuevos.map((t) => t.clave));
  for (const t of previos.values()) {
    if (!claves.has(t.clave)) {
      cambios.push({ tipo: 'quitada', titulo: t.titulo, detalle: 'Ya no aparece en tu CV' });
    }
  }

  if (despues.resumen && despues.resumen !== antes?.resumen) {
    cambios.push({
      tipo: antes?.resumen ? 'editada' : 'nueva',
      titulo: antes?.resumen ? 'Resumen actualizado' : 'Resumen',
      detalle: despues.resumen,
    });
  }
  if (despues.nivel_ingles !== (antes?.nivel_ingles ?? null)) {
    cambios.push(
      despues.nivel_ingles
        ? { tipo: 'editada', titulo: 'Nivel de inglés', detalle: `Ahora ${despues.nivel_ingles}` }
        : { tipo: 'quitada', titulo: 'Nivel de inglés', detalle: 'Ya no aparece en tu CV' },
    );
  }
  return cambios;
}

/** Experiencias y formación con una clave que no depende de tildes ni mayúsculas. */
function tramos(perfil: PerfilCv | null): Tramo[] {
  if (!perfil) return [];
  return [
    ...perfil.experiencias.map((e) => ({
      clave: `e|${normalizar(e.puesto)}|${normalizar(e.sector ?? '')}`,
      titulo: e.sector ? `${e.puesto} · ${e.sector}` : e.puesto,
      fechas: fechas(e.inicio, e.fin, 'actualidad'),
      nueva: 'Experiencia nueva',
      experiencia: true,
    })),
    ...perfil.formacion.map((f) => ({
      clave: `f|${normalizar(f.titulo)}`,
      titulo: f.titulo,
      fechas: fechas(f.inicio, f.fin),
      nueva: 'Formación nueva',
      experiencia: false,
    })),
  ];
}

function fechas(inicio: number | null, fin: number | null, abierto?: string): string {
  if (inicio === null) return fin === null ? '' : `${fin}`;
  if (fin === null) return abierto ? `${inicio} – ${abierto}` : `${inicio}`;
  return inicio === fin ? `${inicio}` : `${inicio} – ${fin}`;
}

function unir(...partes: string[]): string {
  return partes.filter(Boolean).join(' · ');
}

/** «1 experiencia nueva, 3 competencias nuevas y 1 quitada» */
export function resumenCambios(experiencias: number, nuevas: number, quitadas: number): string {
  const partes = [
    contar(experiencias, 'experiencia nueva', 'experiencias nuevas'),
    contar(nuevas, 'competencia nueva', 'competencias nuevas'),
    contar(quitadas, 'quitada', 'quitadas'),
  ].filter(Boolean);
  if (partes.length === 0) return 'Gemelo actualizado';
  const ultima = partes.pop();
  return `Gemelo actualizado: ${partes.length ? `${partes.join(', ')} y ${ultima}` : ultima}`;
}

function contar(n: number, uno: string, varios: string): string {
  return n ? `${n} ${n === 1 ? uno : varios}` : '';
}
