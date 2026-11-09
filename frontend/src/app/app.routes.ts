// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'gemelo' },
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
    loadComponent: () => import('./paginas/entrenador/entrenador').then((m) => m.EntrenadorPagina),
  },
  { path: '**', redirectTo: 'gemelo' },
];
