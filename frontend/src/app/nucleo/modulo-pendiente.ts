// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { Component, input } from '@angular/core';
import { Check, Database, LucideAngularModule } from 'lucide-angular';

/** Página de un módulo aún en desarrollo: qué permitirá hacer y con qué datos. */
@Component({
  selector: 'app-modulo-pendiente',
  imports: [LucideAngularModule],
  template: `
    <header class="cabecera-pagina">
      <div class="min-w-0">
        <div class="flex flex-wrap items-center gap-3">
          <h1 class="titulo-pagina">{{ titulo() }}</h1>
          <span class="etiqueta">Próximamente</span>
        </div>
        <p class="subtitulo-pagina">{{ descripcion() }}</p>
      </div>
    </header>

    <div class="grid items-start gap-4 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
      <section class="tarjeta">
        <h2 class="titulo-seccion">Qué podrás hacer</h2>
        <ul class="mt-5 space-y-4">
          @for (f of funcionalidades(); track f) {
            <li class="flex items-start gap-3 leading-relaxed">
              <span
                class="mt-0.5 grid size-6 shrink-0 place-items-center rounded-full bg-acento-suave text-acento"
              >
                <lucide-icon [img]="iconos.Check" [size]="14" [strokeWidth]="2.5" />
              </span>
              <span>{{ f }}</span>
            </li>
          }
        </ul>
      </section>

      <section class="tarjeta">
        <span class="grid size-10 place-items-center rounded-xl bg-fondo text-tinta-suave">
          <lucide-icon [img]="iconos.Database" [size]="19" />
        </span>
        <h2 class="titulo-seccion mt-4">Con qué datos</h2>
        <p class="mt-2 leading-relaxed text-tinta-suave">{{ datos() }}</p>
      </section>
    </div>
  `,
})
export class ModuloPendiente {
  protected readonly iconos = { Check, Database };
  readonly titulo = input.required<string>();
  readonly descripcion = input.required<string>();
  readonly funcionalidades = input.required<string[]>();
  readonly datos = input.required<string>();
}
