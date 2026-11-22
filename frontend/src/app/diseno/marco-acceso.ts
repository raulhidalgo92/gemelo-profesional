// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { Briefcase, Compass, GraduationCap, LucideAngularModule } from 'lucide-angular';

import { Logo } from '../nucleo/ui/logo';

/** Marco de las pantallas de acceso: presentación a la izquierda y formulario a la derecha. */
@Component({
  selector: 'app-marco-acceso',
  imports: [RouterOutlet, Logo, LucideAngularModule],
  template: `
    <div class="grid min-h-dvh lg:grid-cols-[minmax(0,5fr)_minmax(0,6fr)]">
      <aside
        class="relative hidden overflow-hidden bg-tinta p-12 text-white lg:flex lg:flex-col lg:justify-between"
      >
        <div
          class="pointer-events-none absolute -top-40 -left-40 size-[36rem] rounded-full bg-acento/40 blur-3xl"
        ></div>
        <div
          class="pointer-events-none absolute -right-32 -bottom-48 size-[30rem] rounded-full bg-[#2fb8ff]/20 blur-3xl"
        ></div>

        <app-logo [claro]="true" class="relative" />

        <div class="relative max-w-md">
          <h2 class="text-4xl leading-[1.1] font-semibold tracking-tight">
            Tu carrera, con un plan que entiendes.
          </h2>
          <p class="mt-4 text-[17px] leading-relaxed text-white/65">
            Un gemelo digital de tus competencias que te dice dónde encajas, qué aprender primero y
            cómo llegar al puesto que quieres.
          </p>
          <ul class="mt-10 space-y-4 text-[15px] text-white/80">
            @for (v of ventajas; track v.texto) {
              <li class="flex items-center gap-3">
                <span class="grid size-9 place-items-center rounded-xl bg-white/10">
                  <lucide-icon [img]="v.icono" [size]="18" />
                </span>
                {{ v.texto }}
              </li>
            }
          </ul>
        </div>

        <p class="relative text-[13px] text-white/40">
          Datos públicos del mercado laboral español · Clasificación europea ESCO
        </p>
      </aside>

      <main class="flex min-w-0 flex-col px-6 py-8 sm:px-10">
        <app-logo class="lg:hidden" />
        <div class="flex flex-1 items-center justify-center py-10">
          <div class="w-full max-w-[400px] animate-aparecer">
            <router-outlet />
          </div>
        </div>
      </main>
    </div>
  `,
})
export class MarcoAcceso {
  protected readonly ventajas = [
    { icono: Briefcase, texto: 'Ofertas reales con tu % de encaje explicado' },
    { icono: GraduationCap, texto: 'Qué formación te abre más puertas' },
    { icono: Compass, texto: 'Las trayectorias posibles desde donde estás' },
  ];
}
