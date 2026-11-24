// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { SesionService } from '../../nucleo/sesion.service';
import { BienvenidaPagina } from './bienvenida';

describe('BienvenidaPagina', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [BienvenidaPagina],
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    });
    TestBed.inject(SesionService).usuario.set({
      nombre: 'Ana',
      email: 'ana@ejemplo.com',
      bienvenida_pendiente: true,
    });
  });

  it('saluda por el nombre y avanza al paso del CV', () => {
    const fixture = TestBed.createComponent(BienvenidaPagina);
    fixture.detectChanges();
    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('h1')?.textContent).toContain('Hola, Ana');

    Array.from(el.querySelectorAll('button'))
      .find((b) => b.textContent?.includes('Empezar'))!
      .click();
    fixture.detectChanges();
    expect(el.querySelector('h1')?.textContent).toContain('Sube tu CV');
    expect(el.querySelector('input[type=file]')?.getAttribute('accept')).toBe('.pdf,.docx');
  });

  it('rechaza archivos que no son PDF ni Word', () => {
    const fixture = TestBed.createComponent(BienvenidaPagina);
    const pagina = fixture.componentInstance as unknown as {
      paso: { set(n: number): void };
      soltar(e: DragEvent): void;
      errorArchivo(): string;
      archivo(): File | null;
    };
    pagina.paso.set(1);
    fixture.detectChanges();
    const imagen = new File(['x'], 'foto.png', { type: 'image/png' });
    pagina.soltar({
      preventDefault() {},
      dataTransfer: { files: [imagen] },
    } as unknown as DragEvent);
    expect(pagina.errorArchivo()).toContain('PDF o en Word');
    expect(pagina.archivo()).toBeNull();
  });

  it('analiza el CV y muestra las competencias para revisarlas', () => {
    const fixture = TestBed.createComponent(BienvenidaPagina);
    const pagina = fixture.componentInstance as unknown as {
      paso: { set(n: number): void };
      archivo: { set(f: File): void };
      analizar(): void;
    };
    pagina.paso.set(1);
    pagina.archivo.set(new File(['%PDF'], 'cv.pdf', { type: 'application/pdf' }));
    pagina.analizar();

    const http = TestBed.inject(HttpTestingController);
    const analisis = http.expectOne('/api/gemelo/cv/analizar');
    expect(analisis.request.body instanceof FormData).toBe(true);
    const perfil = { resumen: null, experiencias: [], formacion: [], nivel_ingles: null };
    const detectada = {
      uri: 'u1',
      titulo: 'contabilidad',
      alcance: null,
      termino: 'Contabilidad',
      similitud: 0.8,
    };
    analisis.flush({
      perfil,
      competencias: [{ ...detectada, nueva: true }],
      ya_no: [],
      trayectoria_cambia: true,
    });

    // El primer CV se aplica entero, sin revisión intermedia
    const aplicar = http.expectOne('/api/gemelo/cv/aplicar');
    expect(aplicar.request.body.competencias).toHaveLength(1);
    aplicar.flush([
      {
        uri: 'u1',
        titulo: 'contabilidad',
        tipo: null,
        origen: 'Contabilidad',
        anadida: false,
        demostrada: false,
      },
    ]);
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('h1')?.textContent).toContain('Tus competencias');
    expect(el.textContent).toContain('En tu CV: «Contabilidad»');
  });
});
