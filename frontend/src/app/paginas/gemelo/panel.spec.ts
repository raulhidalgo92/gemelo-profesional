// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import {
  aniosExperiencia,
  buscar,
  haceCuanto,
  hitoInicial,
  hitos,
  porAlcance,
  procedencia,
} from './panel';

describe('panel del gemelo', () => {
  it('cuenta una vez los años en que coinciden dos trabajos', () => {
    const experiencias = [
      { puesto: 'A', sector: null, inicio: 2018, fin: 2021 },
      { puesto: 'B', sector: null, inicio: 2020, fin: null },
      { puesto: 'Sin fecha', sector: null, inicio: null, fin: null },
    ];
    expect(aniosExperiencia(experiencias, 2026)).toBe(8);
  });

  it('coloca los hitos en orden y sin solaparse', () => {
    const lista = hitos(
      {
        resumen: null,
        experiencias: [
          { puesto: 'Auxiliar', sector: 'Logística', inicio: 2018, fin: 2020 },
          { puesto: 'Contable', sector: null, inicio: 2020, fin: null },
        ],
        formacion: [
          { titulo: 'Técnico Superior', inicio: 2016, fin: 2018 },
          { titulo: 'Curso de Excel', inicio: 2020, fin: 2020 },
        ],
        nivel_ingles: null,
      },
      2026,
    );
    expect(lista.map((h) => [h.titulo, h.fechas])).toEqual([
      ['Técnico Superior', '2016 – 2018'],
      ['Auxiliar · Logística', '2018 – 2020'],
      ['Contable', '2020 – actualidad'],
      ['Curso de Excel', '2020'],
    ]);
    const posiciones = lista.map((h) => h.posicion);
    expect(posiciones[0]).toBe(0);
    for (let i = 1; i < posiciones.length; i++) {
      expect(posiciones[i] - posiciones[i - 1]).toBeGreaterThanOrEqual(8.9);
    }
    expect(posiciones.at(-1)).toBeLessThanOrEqual(88);
    expect(hitoInicial(lista)).toBe(2);
  });

  it('agrupa por alcance con las demostradas primero', () => {
    const c = (titulo: string, alcance: string | null, demostrada = false) => ({
      uri: titulo,
      titulo,
      tipo: null,
      alcance,
      origen: null,
      anadida: false,
      demostrada,
    });
    const [transversales, entreSectores] = porAlcance([
      c('trabajo en equipo', 'transversal'),
      c('comunicación', 'transversal'),
      c('inglés', 'transversal', true),
      c('desconocida', null),
    ]);
    expect(transversales.visibles.map((x) => x.titulo)).toEqual([
      'inglés',
      'comunicación',
      'trabajo en equipo',
    ]);
    expect([transversales.total, transversales.demostradas]).toEqual([3, 1]);
    expect(entreSectores.total).toBe(1);
  });

  it('busca sin tildes por nombre o término del CV y filtra por alcance', () => {
    const c = (titulo: string, alcance: string, origen: string | null = null) => ({
      uri: titulo,
      titulo,
      tipo: null,
      alcance,
      origen,
      anadida: false,
      demostrada: false,
    });
    const todas = [
      c('inglés', 'transversal'),
      c('utilizar hojas de cálculo', 'cross-sector', 'Excel'),
      c('contabilidad', 'sector-specific'),
    ];
    expect(buscar(todas, 'INGLES', null).map((x) => x.titulo)).toEqual(['inglés']);
    expect(buscar(todas, 'excel', null).map((x) => x.titulo)).toEqual([
      'utilizar hojas de cálculo',
    ]);
    expect(buscar(todas, '', 'sector-specific').map((x) => x.titulo)).toEqual(['contabilidad']);
  });

  it('explica de dónde sale cada competencia', () => {
    const base = { uri: 'u', titulo: 'SQL', tipo: null, alcance: null };
    expect(procedencia({ ...base, origen: 'SQL', anadida: false, demostrada: true })).toBe(
      'Demostrada en una entrevista',
    );
    expect(procedencia({ ...base, origen: 'SQL', anadida: false, demostrada: false })).toBe(
      'En tu CV: «SQL»',
    );
    expect(procedencia({ ...base, origen: null, anadida: true, demostrada: false })).toBe(
      'Añadida por ti',
    );
  });

  it('dice cuándo se actualizó en lenguaje natural', () => {
    const ahora = new Date(2026, 10, 24, 10);
    expect(haceCuanto(new Date(2026, 10, 24, 8), ahora)).toBe('hoy');
    expect(haceCuanto(new Date(2026, 10, 21), ahora)).toBe('hace 3 días');
    expect(haceCuanto(new Date(2026, 7, 1), ahora)).toBe('hace 3 meses');
  });
});
