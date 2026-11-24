// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { Component, computed, input, linkedSignal, output } from '@angular/core';
import { Briefcase, FileUp, GraduationCap, LucideAngularModule } from 'lucide-angular';

import { PerfilCv } from '../../nucleo/gemelo.service';
import { hitoInicial, hitos } from './panel';

/** Tarjeta «Tu trayectoria»: resumen del CV y línea de tiempo de experiencia y formación. */
@Component({
  selector: 'app-trayectoria',
  imports: [LucideAngularModule],
  template: `
    <section class="tarjeta flex h-full flex-col">
      <div class="mb-[18px] flex items-center justify-between gap-3">
        <h2 class="titulo-seccion">Tu trayectoria</h2>
        @if (actualizado()) {
          <span class="text-[13px] text-tinta-tenue">Actualizado {{ actualizado() }}</span>
        }
      </div>

      @if (perfil(); as p) {
        @if (p.resumen) {
          <p class="texto-tarjeta mb-6">{{ p.resumen }}</p>
        }
        @if (lista().length) {
          <div class="linea relative mx-[18px] hidden h-[74px] md:block">
            <div class="absolute inset-x-0 top-[17px] h-0.5 bg-borde">
              <i class="absolute right-0 h-0.5 bg-[#b9b9c4]" [style.left.%]="inicioTrabajo()"></i>
              <span class="hoy"></span>
            </div>
            <span class="absolute top-11 -right-3 text-xs text-tinta-tenue">Hoy</span>
            @for (h of lista(); track $index) {
              <button
                type="button"
                class="hito absolute top-0 flex -translate-x-1/2 flex-col items-center gap-[7px]"
                [class.activo]="$index === elegido()"
                [style.left.%]="h.posicion"
                [attr.aria-label]="h.titulo + ', ' + h.fechas"
                [attr.aria-pressed]="$index === elegido()"
                (mouseenter)="elegido.set($index)"
                (focus)="elegido.set($index)"
                (click)="elegido.set($index)"
              >
                <span class="punto" [class.formacion]="h.tipo === 'Formación'">
                  <lucide-icon [img]="icono(h.tipo)" [size]="16" />
                </span>
                <span class="text-xs tabular-nums">{{ h.anio }}</span>
              </button>
            }
          </div>
          @if (lista()[elegido()]; as h) {
            <div
              class="mt-2.5 hidden items-center justify-between gap-3.5 border-t border-seleccion pt-3.5 md:flex"
              aria-live="polite"
            >
              <div>
                <b class="block font-semibold">{{ h.titulo }}</b>
                <small class="text-[13px] text-tinta-suave">{{ h.fechas }}</small>
              </div>
              <span class="text-[12.5px] font-medium text-tinta-tenue">{{ h.tipo }}</span>
            </div>
          }

          <ol class="vertical relative grid gap-[18px] md:hidden">
            @for (h of lista(); track $index) {
              <li class="relative flex items-center gap-3">
                <span class="punto" [class.formacion]="h.tipo === 'Formación'">
                  <lucide-icon [img]="icono(h.tipo)" [size]="16" />
                </span>
                <span>
                  <b class="block font-semibold">{{ h.titulo }}</b>
                  <small class="text-[13px] text-tinta-suave">{{ h.fechas }}</small>
                </span>
              </li>
            }
          </ol>
        }
      } @else {
        <!-- Sin CV: la misma línea de tiempo, vacía, para intuir lo que aparecerá -->
        <div class="flex flex-1 flex-col justify-center">
          <div class="fantasma relative mx-[18px] mb-7 h-[60px]" aria-hidden="true">
            <div class="absolute inset-x-0 top-4 border-t-2 border-dashed border-borde">
              <span class="hoy"></span>
            </div>
            <span class="absolute top-11 -right-3 text-xs text-tinta-tenue">Hoy</span>
            @for (h of fantasmas; track $index) {
              <span
                class="punto absolute top-0 -translate-x-1/2"
                [class.formacion]="h.formacion"
                [style.left.%]="h.posicion"
              >
                <lucide-icon
                  [img]="h.formacion ? iconos.GraduationCap : iconos.Briefcase"
                  [size]="16"
                />
              </span>
            }
          </div>
          <div class="flex flex-wrap items-center justify-between gap-x-6 gap-y-4">
            <p class="texto-tarjeta max-w-md">
              Sube tu CV y construimos tu trayectoria: tus puestos, tu formación y tu nivel de
              inglés.
            </p>
            <button type="button" class="boton-secundario" (click)="subir.emit()">
              <lucide-icon [img]="iconos.FileUp" [size]="18" />
              Subir CV
            </button>
          </div>
        </div>
      }
    </section>
  `,
  styles: `
    .punto {
      display: grid;
      place-items: center;
      flex: none;
      width: 36px;
      height: 36px;
      border-radius: 50%;
      background: var(--color-seleccion);
      color: var(--color-tinta-suave);
      transition:
        background 0.18s,
        color 0.18s;
    }
    .punto.formacion {
      border-radius: 11px;
    }
    .hito {
      color: var(--color-tinta-suave);
    }
    .hito:focus-visible {
      outline: none;
    }
    .hito:focus-visible .punto {
      box-shadow: 0 0 0 3px rgb(23 23 28 / 10%);
    }
    .hito:hover .punto,
    .hito.activo .punto {
      background: #332c78;
      color: #efedff;
    }
    .hito.activo {
      color: var(--color-tinta);
      font-weight: 600;
    }
    .hoy {
      position: absolute;
      top: -4px;
      right: -5px;
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: var(--color-tinta-tenue);
      box-shadow: 0 0 0 4px var(--color-seleccion);
    }
    .fantasma .punto {
      background: var(--color-fondo);
      color: #c9c9d3;
    }
    .vertical::before {
      content: '';
      position: absolute;
      top: 12px;
      bottom: 12px;
      left: 17px;
      width: 2px;
      background: var(--color-borde);
    }
  `,
})
export class Trayectoria {
  readonly perfil = input.required<PerfilCv | null>();
  /** «hace 3 días», «hoy»… */
  readonly actualizado = input<string>();
  readonly subir = output();

  protected readonly iconos = { Briefcase, FileUp, GraduationCap };
  /** Hitos de muestra para la línea vacía */
  protected readonly fantasmas = [
    { posicion: 0, formacion: true },
    { posicion: 30, formacion: false },
    { posicion: 62, formacion: false },
  ];
  private readonly hoy = new Date().getFullYear();
  protected readonly lista = computed(() => {
    const p = this.perfil();
    return p ? hitos(p, this.hoy) : [];
  });
  /** Se vuelve al trabajo actual cada vez que cambia la trayectoria */
  protected readonly elegido = linkedSignal(() => hitoInicial(this.lista()));
  /** La línea se oscurece desde el primer trabajo hasta hoy */
  protected readonly inicioTrabajo = computed(
    () => this.lista().find((h) => h.tipo === 'Experiencia')?.posicion ?? 100,
  );

  protected icono(tipo: string) {
    return tipo === 'Formación' ? GraduationCap : Briefcase;
  }
}
