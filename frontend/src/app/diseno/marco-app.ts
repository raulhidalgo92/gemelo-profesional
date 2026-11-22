// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { Component, inject } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import {
  Briefcase,
  Compass,
  GraduationCap,
  LogOut,
  LucideAngularModule,
  Mic,
  Sparkles,
} from 'lucide-angular';

import { SesionService } from '../nucleo/sesion.service';
import { Logo } from '../nucleo/ui/logo';

/** Marco de la aplicación con sesión iniciada: menú lateral y contenido. */
@Component({
  selector: 'app-marco-app',
  imports: [RouterOutlet, RouterLink, RouterLinkActive, Logo, LucideAngularModule],
  template: `
    <div class="grid min-h-dvh md:grid-cols-[248px_minmax(0,1fr)]">
      <aside
        class="flex flex-col gap-8 border-b border-borde bg-superficie px-4 py-5 md:sticky md:top-0 md:h-dvh md:border-r md:border-b-0"
      >
        <app-logo class="px-2" />
        <nav class="flex gap-1 overflow-x-auto md:flex-col">
          @for (e of menu; track e.ruta) {
            <a
              [routerLink]="e.ruta"
              routerLinkActive="!bg-tinta !text-white"
              class="flex shrink-0 items-center gap-3 rounded-xl px-3 py-2.5 text-[15px] font-medium text-tinta-suave transition hover:bg-fondo hover:text-tinta"
            >
              <lucide-icon [img]="e.icono" [size]="18" />
              {{ e.texto }}
            </a>
          }
        </nav>
        <div class="mt-auto hidden items-center gap-3 border-t border-borde px-2 pt-4 md:flex">
          <span
            class="grid size-9 shrink-0 place-items-center rounded-full bg-acento-suave text-sm font-semibold text-acento"
            >{{ inicial() }}</span
          >
          <div class="min-w-0 flex-1">
            <p class="truncate text-sm font-medium">{{ sesion.usuario()?.nombre }}</p>
            <p class="truncate text-xs text-tinta-tenue">{{ sesion.usuario()?.email }}</p>
          </div>
          <button
            type="button"
            (click)="salir()"
            class="grid size-9 place-items-center rounded-lg text-tinta-tenue transition hover:bg-fondo hover:text-tinta"
            aria-label="Cerrar sesión"
            title="Cerrar sesión"
          >
            <lucide-icon [img]="iconoSalir" [size]="18" />
          </button>
        </div>
      </aside>
      <main class="min-w-0 px-5 py-8 sm:px-10 lg:px-14">
        <div class="mx-auto max-w-5xl animate-aparecer">
          <router-outlet />
        </div>
      </main>
    </div>
  `,
})
export class MarcoApp {
  protected readonly sesion = inject(SesionService);
  private readonly router = inject(Router);
  protected readonly iconoSalir = LogOut;
  protected readonly menu = [
    { ruta: '/gemelo', icono: Sparkles, texto: 'Mi gemelo' },
    { ruta: '/futuro', icono: Compass, texto: 'Mi futuro' },
    { ruta: '/empleo', icono: Briefcase, texto: 'Empleo' },
    { ruta: '/formacion', icono: GraduationCap, texto: 'Formarte' },
    { ruta: '/entrenador', icono: Mic, texto: 'Entrenador' },
  ];

  protected inicial(): string {
    return (this.sesion.usuario()?.nombre ?? '?').charAt(0).toUpperCase();
  }

  protected salir(): void {
    this.sesion.salir().subscribe(() => this.router.navigateByUrl('/entrar'));
  }
}
