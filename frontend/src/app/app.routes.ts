// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { Routes } from '@angular/router';

import { MarcoAcceso } from './diseno/marco-acceso';
import { MarcoApp } from './diseno/marco-app';
import { bienvenidaHecha, conSesion, fueraDeLaApp, sinSesion } from './nucleo/guardas';

export const routes: Routes = [
  // Acceso (sin sesión)
  {
    path: '',
    component: MarcoAcceso,
    canActivate: [sinSesion],
    children: [
      // La raíz lleva a «Entrar»; con sesión, la guarda redirige a la aplicación
      { path: '', pathMatch: 'full', redirectTo: 'entrar' },
      {
        path: 'entrar',
        title: 'Entrar · Gemelo profesional',
        loadComponent: () => import('./paginas/acceso/entrar').then((m) => m.EntrarPagina),
      },
      {
        path: 'registro',
        title: 'Crea tu cuenta · Gemelo profesional',
        loadComponent: () => import('./paginas/acceso/registro').then((m) => m.RegistroPagina),
      },
      {
        path: 'registro/codigo',
        title: 'Revisa tu correo · Gemelo profesional',
        loadComponent: () =>
          import('./paginas/acceso/verificar-codigo').then((m) => m.VerificarCodigoPagina),
      },
    ],
  },
  {
    path: 'verificar',
    component: MarcoAcceso,
    children: [
      {
        path: '',
        title: 'Activando tu cuenta · Gemelo profesional',
        loadComponent: () =>
          import('./paginas/acceso/verificar-enlace').then((m) => m.VerificarEnlacePagina),
      },
    ],
  },
  {
    path: 'privacidad',
    title: 'Privacidad · Gemelo profesional',
    canMatch: [fueraDeLaApp],
    loadComponent: () =>
      import('./paginas/acceso/privacidad').then((m) => m.PrivacidadPublicaPagina),
  },

  // Bienvenida tras activar la cuenta
  {
    path: 'bienvenida',
    title: 'Bienvenida · Gemelo profesional',
    canActivate: [conSesion],
    loadComponent: () => import('./paginas/bienvenida/bienvenida').then((m) => m.BienvenidaPagina),
  },

  // Aplicación (con sesión)
  {
    path: '',
    component: MarcoApp,
    canActivate: [conSesion, bienvenidaHecha],
    children: [
      {
        path: 'gemelo',
        title: 'Mi gemelo',
        loadComponent: () => import('./paginas/gemelo/gemelo').then((m) => m.GemeloPagina),
      },
      {
        path: 'futuro',
        title: 'Mi futuro',
        loadComponent: () => import('./paginas/futuro/futuro').then((m) => m.FuturoPagina),
      },
      {
        path: 'empleo',
        title: 'Empleo',
        loadComponent: () => import('./paginas/empleo/empleo').then((m) => m.EmpleoPagina),
      },
      {
        path: 'formacion',
        title: 'Formarte',
        loadComponent: () => import('./paginas/formacion/formacion').then((m) => m.FormacionPagina),
      },
      {
        path: 'entrenador',
        title: 'Entrenador',
        loadComponent: () =>
          import('./paginas/entrenador/entrenador').then((m) => m.EntrenadorPagina),
      },
      {
        path: 'cuenta',
        title: 'Mi cuenta',
        loadComponent: () => import('./paginas/cuenta/cuenta').then((m) => m.CuentaPagina),
      },
      {
        path: 'privacidad',
        title: 'Privacidad · Gemelo profesional',
        loadComponent: () => import('./paginas/acceso/privacidad').then((m) => m.PrivacidadPagina),
      },
    ],
  },
  { path: '**', redirectTo: '' },
];
