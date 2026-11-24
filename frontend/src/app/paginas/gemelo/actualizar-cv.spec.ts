// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { vi } from 'vitest';

import { AnalisisCv, GemeloService, PerfilCv } from '../../nucleo/gemelo.service';
import { ActualizarCv } from './actualizar-cv';

const PERFIL: PerfilCv = {
  resumen: 'Administrativa contable.',
  experiencias: [{ puesto: 'Administrativa', sector: 'Logística', inicio: 2020, fin: null }],
  formacion: [],
  nivel_ingles: 'B2',
};

const ANALISIS: AnalisisCv = {
  perfil: {
    ...PERFIL,
    experiencias: [
      { puesto: 'Administrativa', sector: 'Logística', inicio: 2020, fin: 2026 },
      { puesto: 'Responsable de equipo', sector: 'Logística', inicio: 2026, fin: null },
    ],
  },
  competencias: [
    { uri: 'sql', titulo: 'SQL', alcance: null, termino: 'SQL', similitud: 0.9, nueva: false },
    {
      uri: 'bi',
      titulo: 'power BI',
      alcance: null,
      termino: 'Power BI',
      similitud: 0.8,
      nueva: true,
    },
    {
      uri: 'pp',
      titulo: 'presupuestos',
      alcance: null,
      termino: 'Presupuestos',
      similitud: 0.8,
      nueva: true,
    },
  ],
  ya_no: [
    {
      uri: 'archivo',
      titulo: 'archivar documentos',
      tipo: null,
      alcance: null,
      origen: 'Archivo',
      anadida: false,
      demostrada: false,
    },
  ],
  trayectoria_cambia: true,
};

function crear(analisis: AnalisisCv) {
  const gemelo = {
    analizarCv: vi.fn(() => of(analisis)),
    aplicarCv: vi.fn(() => of([])),
  };
  TestBed.configureTestingModule({
    imports: [ActualizarCv],
    providers: [{ provide: GemeloService, useValue: gemelo }],
  });
  const fixture = TestBed.createComponent(ActualizarCv);
  fixture.componentRef.setInput('perfil', PERFIL);
  fixture.detectChanges();
  // jsdom no implementa <dialog>: basta con que existan los métodos
  const dialogo = fixture.nativeElement.querySelector('dialog') as HTMLDialogElement;
  dialogo.showModal = () => dialogo.setAttribute('open', '');
  dialogo.close = () => dialogo.dispatchEvent(new Event('close'));
  fixture.componentInstance.abrir();
  fixture.detectChanges();

  const el = fixture.nativeElement as HTMLElement;
  const entrada = el.querySelector('input[type=file]') as HTMLInputElement;
  const archivo = new File(['%PDF'], 'cv.pdf', { type: 'application/pdf' });
  Object.defineProperty(entrada, 'files', { value: [archivo] });
  entrada.dispatchEvent(new Event('change'));
  fixture.detectChanges();
  return { fixture, el, gemelo };
}

describe('ActualizarCv', () => {
  it('muestra los cambios y aplica solo lo que el usuario deja marcado', () => {
    const { fixture, el, gemelo } = crear(ANALISIS);
    const texto = el.textContent!.replace(/\s+/g, ' ');
    expect(texto).toContain('Responsable de equipo · Logística');
    expect(texto).toContain('Ahora 2020 – 2026');
    expect(texto.replace(/ /g, '')).toContain('Competenciasnuevas2');
    expect(texto).toContain('1 competencia sigue igual');
    expect(gemelo.aplicarCv).not.toHaveBeenCalled();

    // Descarta «presupuestos» y deja que se quite «archivar documentos»
    const casillas = el.querySelectorAll<HTMLInputElement>('input[type=checkbox]');
    casillas[1].click();
    casillas[2].click();
    fixture.detectChanges();
    const aplicado = vi.fn();
    fixture.componentInstance.aplicado.subscribe(aplicado);
    [...el.querySelectorAll('button')]
      .find((b) => b.textContent!.includes('Actualizar mi'))!
      .click();
    fixture.detectChanges();

    expect(gemelo.aplicarCv).toHaveBeenCalledWith(
      ANALISIS.perfil,
      [ANALISIS.competencias[0], ANALISIS.competencias[1]],
      [],
    );
    expect(aplicado).toHaveBeenCalled();
    expect(el.textContent).toContain(
      'Gemelo actualizado: 1 experiencia nueva, 1 competencia nueva y 1 quitada',
    );
  });

  it('si el CV no trae nada nuevo lo dice y no guarda nada', () => {
    const { el, gemelo } = crear({
      perfil: PERFIL,
      competencias: [ANALISIS.competencias[0]],
      ya_no: [],
      trayectoria_cambia: false,
    });
    expect(el.textContent).toContain('Tu CV no trae cambios');
    expect(gemelo.aplicarCv).not.toHaveBeenCalled();
  });
});
