// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { provideHttpClient } from '@angular/common/http';
import { EnvironmentInjector, runInInjectionContext } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import {
  ActivatedRouteSnapshot,
  CanActivateFn,
  Router,
  RouterStateSnapshot,
  provideRouter,
} from '@angular/router';

import { bienvenidaHecha, conSesion, fueraDeLaApp, sinSesion } from './guardas';
import { SesionService, Usuario } from './sesion.service';

const USUARIO: Usuario = { nombre: 'Ana', email: 'ana@ejemplo.com', bienvenida_pendiente: false };

describe('guardas de rutas', () => {
  function ejecutar(guarda: CanActivateFn, usuario: Usuario | null) {
    const sesion = TestBed.inject(SesionService);
    // Respuesta asíncrona real: las guardas continúan tras un await
    vi.spyOn(sesion, 'cargar').mockImplementation(() => Promise.resolve(usuario));
    return runInInjectionContext(TestBed.inject(EnvironmentInjector), () =>
      guarda({} as ActivatedRouteSnapshot, { url: '/empleo' } as RouterStateSnapshot),
    ) as Promise<unknown>;
  }

  const url = (destino: unknown) => TestBed.inject(Router).serializeUrl(destino as never);

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [provideRouter([]), provideHttpClient()] });
  });

  it('con sesión, las pantallas de acceso llevan a la aplicación', async () => {
    expect(url(await ejecutar(sinSesion, USUARIO))).toBe('/gemelo');
  });

  it('sin sesión, la aplicación lleva a entrar y recuerda la ruta', async () => {
    expect(url(await ejecutar(conSesion, null))).toBe('/entrar?volver=%2Fempleo');
  });

  it('con la bienvenida pendiente, lleva al asistente', async () => {
    const pendiente = { ...USUARIO, bienvenida_pendiente: true };
    expect(url(await ejecutar(bienvenidaHecha, pendiente))).toBe('/bienvenida');
    expect(await ejecutar(bienvenidaHecha, USUARIO)).toBe(true);
  });

  it('las páginas sin menú son para quien aún no ha entrado en la aplicación', async () => {
    const pendiente = { ...USUARIO, bienvenida_pendiente: true };
    expect(await ejecutar(fueraDeLaApp as unknown as CanActivateFn, null)).toBe(true);
    expect(await ejecutar(fueraDeLaApp as unknown as CanActivateFn, pendiente)).toBe(true);
    expect(await ejecutar(fueraDeLaApp as unknown as CanActivateFn, USUARIO)).toBe(false);
  });
});
