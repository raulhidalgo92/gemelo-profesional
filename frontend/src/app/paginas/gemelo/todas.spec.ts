// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { Component, signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { vi } from 'vitest';

import { ApiService } from '../../nucleo/api.service';
import { CompetenciaGemelo, GemeloService } from '../../nucleo/gemelo.service';
import { TodasCompetencias } from './todas';

function competencia(titulo: string, demostrada = false): CompetenciaGemelo {
  const datos = { tipo: null, alcance: 'transversal', origen: titulo, anadida: false };
  return { uri: titulo, titulo, ...datos, demostrada };
}

@Component({
  imports: [TodasCompetencias],
  template: `<app-todas-competencias #todas [(competencias)]="lista" />`,
})
class Anfitrion {
  readonly lista = signal([competencia('inglés', true), competencia('contabilidad')]);
}

describe('TodasCompetencias', () => {
  let gemelo: { quitar: ReturnType<typeof vi.fn>; anadir: ReturnType<typeof vi.fn> };

  function crear() {
    gemelo = {
      quitar: vi.fn(() => of(undefined)),
      anadir: vi.fn(() => of({ ...competencia('SQL'), anadida: true, origen: null })),
    };
    TestBed.configureTestingModule({
      imports: [Anfitrion],
      providers: [
        { provide: GemeloService, useValue: gemelo },
        {
          provide: ApiService,
          useValue: { buscarCompetencias: () => of({ modo: 'semantico', resultados: [] }) },
        },
      ],
    });
    const fixture = TestBed.createComponent(Anfitrion);
    fixture.detectChanges();
    const el = fixture.nativeElement as HTMLElement;
    const pulsar = (texto: string) => {
      const boton = [...el.querySelectorAll('button')].find(
        (b) => b.textContent!.trim() === texto || b.getAttribute('aria-label') === texto,
      );
      boton!.click();
      fixture.detectChanges();
    };
    return { fixture, el, pulsar };
  }

  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it('quitar se puede deshacer y no borra nada en el servidor', () => {
    const { fixture, el, pulsar } = crear();
    pulsar('Quitar contabilidad');
    expect(fixture.componentInstance.lista().map((c) => c.titulo)).toEqual(['inglés']);
    expect(el.textContent).toContain('Has quitado «Contabilidad»');

    pulsar('Deshacer');
    expect(fixture.componentInstance.lista()).toHaveLength(2);
    vi.advanceTimersByTime(7000);
    expect(gemelo.quitar).not.toHaveBeenCalled();
  });

  it('si no se deshace, se borra al terminar el aviso', () => {
    const { pulsar } = crear();
    pulsar('Quitar contabilidad');
    vi.advanceTimersByTime(6000);
    expect(gemelo.quitar).toHaveBeenCalledWith('contabilidad');
  });

  it('una demostrada pide confirmación antes de quitarla', () => {
    const { fixture, el, pulsar } = crear();
    pulsar('Quitar inglés');
    expect(el.textContent).toContain('Perderás la evidencia de tu entrevista');
    expect(fixture.componentInstance.lista()).toHaveLength(2);
    pulsar('Quitar');
    expect(fixture.componentInstance.lista().map((c) => c.titulo)).toEqual(['contabilidad']);
  });

  it('añadir desde el catálogo se refleja en la lista', () => {
    const { fixture, el, pulsar } = crear();
    pulsar('Añadir competencia');
    expect(el.querySelector('input[aria-label="Buscar en el catálogo ESCO"]')).toBeTruthy();
    const todas = fixture.debugElement.children[0].componentInstance as TodasCompetencias;
    (todas as unknown as { anadir: (r: unknown) => void }).anadir({ uri: 'SQL', titulo: 'SQL' });
    fixture.detectChanges();
    expect(gemelo.anadir).toHaveBeenCalledWith('SQL');
    expect(fixture.componentInstance.lista().map((c) => c.titulo)).toContain('SQL');
    expect(el.textContent).toContain('Has añadido «SQL»');
  });
});
