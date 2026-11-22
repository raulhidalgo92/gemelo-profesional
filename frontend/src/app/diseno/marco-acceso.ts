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
          class="pointer-events-none absolute -top-48 -left-40 size-[38rem] rounded-full bg-acento/35 blur-3xl"
        ></div>
        <!-- El símbolo de la marca, a gran escala, como fondo -->
        <svg
          class="pointer-events-none absolute -right-72 -bottom-64 size-[44rem] opacity-[0.08]"
          viewBox="0 0 32 32"
          aria-hidden="true"
        >
          <circle cx="12" cy="16" r="9" fill="none" stroke="#fff" stroke-width="0.25" />
          <circle cx="20" cy="16" r="9" fill="none" stroke="#fff" stroke-width="0.25" />
        </svg>

        <app-logo [claro]="true" [tamano]="36" class="relative" />

        <div class="relative max-w-lg">
          <h2 class="text-[40px] leading-[1.1] font-semibold tracking-tight xl:text-[46px]">
            Tú pones el destino.<br />Tu gemelo, el camino.
          </h2>
          <p class="mt-6 max-w-md text-lg leading-relaxed text-balance text-white/65">
            Un modelo digital de tus competencias que evoluciona contigo y convierte tu objetivo en
            pasos concretos.
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
        <app-logo [tamano]="32" class="lg:hidden" />
        <div class="flex flex-1 items-center justify-center py-10">
          <div class="w-full max-w-[420px] animate-aparecer">
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
