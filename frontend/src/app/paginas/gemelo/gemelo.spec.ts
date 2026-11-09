// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';

import { ApiService, ModoBusqueda } from '../../nucleo/api.service';
import { GemeloPagina } from './gemelo';

describe('GemeloPagina', () => {
  const llamadas: { q: string; modo: ModoBusqueda }[] = [];
  const apiFalsa = {
    salud: () => of({ estado: 'ok', version: '0.1.0', base_datos: true }),
    resumenMercado: () => of(null),
    buscarCompetencias: (q: string, modo: ModoBusqueda) => {
      llamadas.push({ q, modo });
      return of({
        modo,
        resultados: [{ uri: 'u1', titulo: 'TypeScript', tipo: 'knowledge', similitud: 0.61 }],
      });
    },
  };

  beforeEach(async () => {
    vi.useFakeTimers();
    llamadas.length = 0;
    await TestBed.configureTestingModule({
      imports: [GemeloPagina],
      providers: [{ provide: ApiService, useValue: apiFalsa }],
    }).compileComponents();
  });

  afterEach(() => vi.useRealTimers());

  async function escribir(fixture: ReturnType<typeof TestBed.createComponent<GemeloPagina>>) {
    fixture.detectChanges();
    await vi.advanceTimersByTimeAsync(400);
    fixture.detectChanges();
  }

  it('busca por significado y repite la búsqueda al cambiar a texto', async () => {
    const fixture = TestBed.createComponent(GemeloPagina);
    const html = fixture.nativeElement as HTMLElement;
    const entrada = html.querySelector('input[type=search]') as HTMLInputElement;

    entrada.value = 'Angular';
    entrada.dispatchEvent(new Event('input'));
    await escribir(fixture);

    expect(llamadas).toEqual([{ q: 'Angular', modo: 'semantico' }]);
    expect(html.querySelector('.resultados li')?.textContent).toContain('TypeScript');
    expect(html.querySelector('.etiqueta')?.textContent).toContain('conocimiento');

    (html.querySelectorAll('.selector button')[1] as HTMLButtonElement).click();
    await escribir(fixture);

    expect(llamadas.at(-1)).toEqual({ q: 'Angular', modo: 'texto' });
  });

  it('no busca con menos de dos caracteres', async () => {
    const fixture = TestBed.createComponent(GemeloPagina);
    const entrada = (fixture.nativeElement as HTMLElement).querySelector(
      'input[type=search]',
    ) as HTMLInputElement;
    entrada.value = 'A';
    entrada.dispatchEvent(new Event('input'));
    await escribir(fixture);
    expect(llamadas).toEqual([]);
  });
});
