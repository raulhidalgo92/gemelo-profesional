// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import {
  Briefcase,
  Compass,
  GraduationCap,
  LucideAngularModule,
  Mic,
  Sparkles,
} from 'lucide-angular';

import { Logo } from '../nucleo/ui/logo';
import { MenuUsuario } from './menu-usuario';

/** Marco de la aplicación con sesión iniciada: menú lateral y contenido. */
@Component({
  selector: 'app-marco-app',
  imports: [RouterOutlet, RouterLink, RouterLinkActive, Logo, MenuUsuario, LucideAngularModule],
  template: `
    <div
      class="grid min-h-dvh grid-cols-[minmax(0,1fr)] md:grid-cols-[264px_minmax(0,1fr)] md:grid-rows-1 grid-rows-[auto_1fr]"
    >
      <aside
        class="flex min-w-0 flex-col gap-5 md:gap-8 border-b border-borde bg-superficie px-4 py-5 md:sticky md:top-0 md:h-dvh md:border-r md:border-b-0"
      >
        <div class="flex items-center justify-between px-2">
          <a
            routerLink="/gemelo"
            aria-label="Gemelo profesional: ir a Mi gemelo"
            class="rounded-lg focus-visible:ring-4 focus-visible:ring-acento/25 focus-visible:outline-none"
          >
            <app-logo [tamano]="30" />
          </a>
          <app-menu-usuario [compacto]="true" class="md:hidden" />
        </div>
        <nav class="flex gap-1 overflow-x-auto md:flex-col">
          @for (e of menu; track e.ruta) {
            <a
              [routerLink]="e.ruta"
              routerLinkActive="!bg-seleccion !font-semibold !text-tinta"
              class="flex shrink-0 items-center gap-3 rounded-xl px-3 py-2.5 text-[15px] font-medium text-tinta-suave transition hover:bg-fondo hover:text-tinta"
            >
              <lucide-icon [img]="e.icono" [size]="18" />
              {{ e.texto }}
            </a>
          }
        </nav>
        <app-menu-usuario class="mt-auto hidden border-t border-borde pt-3 md:block" />
      </aside>
      <main class="min-w-0 px-5 py-8 sm:px-10 sm:py-12 lg:px-14">
        <div class="mx-auto max-w-5xl animate-aparecer">
          <router-outlet />
        </div>
      </main>
    </div>
  `,
})
export class MarcoApp {
  protected readonly menu = [
    { ruta: '/gemelo', icono: Sparkles, texto: 'Mi gemelo' },
    { ruta: '/futuro', icono: Compass, texto: 'Mi futuro' },
    { ruta: '/empleo', icono: Briefcase, texto: 'Empleo' },
    { ruta: '/formacion', icono: GraduationCap, texto: 'Formarte' },
    { ruta: '/entrenador', icono: Mic, texto: 'Entrenador' },
  ];
}
