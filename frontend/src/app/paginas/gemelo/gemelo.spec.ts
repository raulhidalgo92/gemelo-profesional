// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';

import { CompetenciaGemelo, GemeloService, ResumenGemelo } from '../../nucleo/gemelo.service';
import { SesionService } from '../../nucleo/sesion.service';
import { GemeloPagina } from './gemelo';

const PERFIL = {
  resumen: 'Administrativa contable con 8 años de experiencia.',
  experiencias: [
    { puesto: 'Auxiliar administrativa', sector: 'Logística', inicio: 2018, fin: 2020 },
    { puesto: 'Administrativa contable', sector: 'Logística', inicio: 2020, fin: null },
  ],
  formacion: [{ titulo: 'Técnico Superior en Administración', inicio: 2016, fin: 2018 }],
  nivel_ingles: 'B2',
};

function competencia(titulo: string, alcance: string, demostrada = false): CompetenciaGemelo {
  return {
    uri: titulo,
    titulo,
    tipo: 'skill',
    alcance,
    origen: titulo,
    anadida: false,
    demostrada,
  };
}

function crear(resumen: ResumenGemelo, competencias: CompetenciaGemelo[]): HTMLElement {
  TestBed.configureTestingModule({
    imports: [GemeloPagina],
    providers: [
      provideRouter([]),
      { provide: SesionService, useValue: { usuario: signal({ nombre: 'Laura' }) } },
      {
        provide: GemeloService,
        useValue: { resumen: () => of(resumen), competencias: () => of(competencias) },
      },
    ],
  });
  const fixture = TestBed.createComponent(GemeloPagina);
  fixture.detectChanges();
  return fixture.nativeElement as HTMLElement;
}

describe('GemeloPagina', () => {
  it('resume el perfil, la trayectoria y las competencias por alcance', () => {
    const el = crear({ perfil: PERFIL, actualizado_en: new Date().toISOString() }, [
      competencia('inglés', 'transversal', true),
      competencia('contabilidad', 'sector-specific'),
      competencia('facturación', 'sector-specific'),
    ]);
    const texto = el.textContent!.replace(/\s+/g, '');

    expect(texto).toContain('Hola,Laura');
    expect(texto).toContain('Administrativacontable·8añosdeexperiencia·InglésB2');
    expect(texto).toContain('Actualizadohoy');
    // Al entrar se muestra el trabajo actual
    expect(texto).toContain('Administrativacontable·Logística2020–actualidadExperiencia');
    expect(texto).toContain('1de3demostradas');
    expect(texto).toContain('DetusectorTuespecialidad0de2');
    // Tareas: cuenta, CV y una competencia demostrada; falta elegir destino
    expect(texto).toContain('Tuavance3de5');
    expect(texto).toContain('SiguientetareaEligetudestino');
    expect(texto).toContain('Último:Primeraevidencia');
  });

  it('sin CV invita a subirlo', () => {
    const el = crear({ perfil: null, actualizado_en: null }, []);
    expect(el.textContent).toContain('Subir mi CV');
    expect(el.textContent!.replace(/\s+/g, '')).toContain('SiguientetareaSubetuCV');
    expect(el.querySelectorAll('.logro.conseguido')).toHaveLength(0);
  });
});
