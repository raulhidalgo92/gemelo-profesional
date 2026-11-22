// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { provideHttpClient } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { MarcoApp } from './diseno/marco-app';
import { SesionService } from './nucleo/sesion.service';

describe('MarcoApp', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MarcoApp],
      providers: [provideRouter([]), provideHttpClient()],
    }).compileComponents();
    TestBed.inject(SesionService).usuario.set({
      nombre: 'Ana',
      email: 'ana@ejemplo.com',
      bienvenida_pendiente: false,
    });
  });

  it('muestra los cinco apartados del menú y el usuario', () => {
    const fixture = TestBed.createComponent(MarcoApp);
    fixture.detectChanges();
    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelectorAll('nav a').length).toBe(5);
    expect(el.textContent).toContain('ana@ejemplo.com');
    // Cerrar sesión queda dentro del menú del usuario
    expect(el.textContent).not.toContain('Cerrar sesión');
    (el.querySelector('[aria-haspopup=menu]') as HTMLButtonElement).click();
    fixture.detectChanges();
    expect(el.textContent).toContain('Cerrar sesión');
  });
});
