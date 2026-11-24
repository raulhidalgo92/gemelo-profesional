// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { PerfilCv } from '../../nucleo/gemelo.service';
import { cambiosTrayectoria, resumenCambios } from './cambios';

const ANTES: PerfilCv = {
  resumen: 'Administrativa contable.',
  experiencias: [
    { puesto: 'Administrativa contable', sector: 'Logística', inicio: 2020, fin: null },
    { puesto: 'Recepcionista', sector: 'Hostelería', inicio: 2016, fin: 2018 },
  ],
  formacion: [{ titulo: 'Técnico Superior en Administración', inicio: 2016, fin: 2018 }],
  nivel_ingles: 'B2',
};

describe('cambios de un CV nuevo', () => {
  it('detecta experiencias nuevas, fechas cambiadas, quitadas, resumen e inglés', () => {
    const despues: PerfilCv = {
      resumen: 'Responsable de equipo administrativo.',
      experiencias: [
        { puesto: 'Administrativa contable', sector: 'logistica', inicio: 2020, fin: 2026 },
        { puesto: 'Responsable de equipo', sector: 'Logística', inicio: 2026, fin: null },
      ],
      formacion: ANTES.formacion,
      nivel_ingles: 'C1',
    };
    expect(cambiosTrayectoria(ANTES, despues)).toEqual([
      {
        tipo: 'editada',
        titulo: 'Administrativa contable · logistica',
        detalle: 'Ahora 2020 – 2026',
      },
      {
        tipo: 'nueva',
        titulo: 'Responsable de equipo · Logística',
        detalle: '2026 – actualidad · Experiencia nueva',
        experiencia: true,
      },
      {
        tipo: 'quitada',
        titulo: 'Recepcionista · Hostelería',
        detalle: 'Ya no aparece en tu CV',
      },
      {
        tipo: 'editada',
        titulo: 'Resumen actualizado',
        detalle: 'Responsable de equipo administrativo.',
      },
      { tipo: 'editada', titulo: 'Nivel de inglés', detalle: 'Ahora C1' },
    ]);
  });

  it('el mismo CV no trae cambios', () => {
    expect(cambiosTrayectoria(ANTES, structuredClone(ANTES))).toEqual([]);
  });

  it('resume lo aplicado en una frase', () => {
    expect(resumenCambios(1, 3, 1)).toBe(
      'Gemelo actualizado: 1 experiencia nueva, 3 competencias nuevas y 1 quitada',
    );
    expect(resumenCambios(0, 1, 0)).toBe('Gemelo actualizado: 1 competencia nueva');
    expect(resumenCambios(0, 0, 0)).toBe('Gemelo actualizado');
  });
});
