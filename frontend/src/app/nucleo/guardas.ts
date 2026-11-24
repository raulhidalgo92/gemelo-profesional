// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { inject } from '@angular/core';
import { CanActivateFn, CanMatchFn, Router } from '@angular/router';

import { SesionService } from './sesion.service';

// Los inject() van antes del primer await: después, Angular ya no permite inyectar.

/** Solo con sesión iniciada; si no, a la pantalla de entrada. */
export const conSesion: CanActivateFn = async (_ruta, estado) => {
  const router = inject(Router);
  const sesion = inject(SesionService);
  const usuario = await sesion.cargar();
  return usuario
    ? true
    : router.createUrlTree(['/entrar'], { queryParams: { volver: estado.url } });
};

/** Pantallas de acceso: si ya hay sesión, a la aplicación. */
export const sinSesion: CanActivateFn = async () => {
  const router = inject(Router);
  const sesion = inject(SesionService);
  const usuario = await sesion.cargar();
  return usuario ? router.createUrlTree(['/gemelo']) : true;
};

/** La aplicación espera a que el usuario termine (o posponga) la bienvenida. */
export const bienvenidaHecha: CanActivateFn = async () => {
  const router = inject(Router);
  const sesion = inject(SesionService);
  const usuario = await sesion.cargar();
  return usuario?.bienvenida_pendiente ? router.createUrlTree(['/bienvenida']) : true;
};

/** Versión sin menú de una página: para quien aún no ha entrado en la aplicación. */
export const fueraDeLaApp: CanMatchFn = async () => {
  const sesion = inject(SesionService);
  const usuario = await sesion.cargar();
  return !usuario || usuario.bienvenida_pendiente;
};
