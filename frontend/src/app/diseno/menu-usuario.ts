// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { Component, ElementRef, inject, input, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import {
  ArrowRight,
  ChevronsUpDown,
  LucideAngularModule,
  Power,
  ShieldCheck,
  UserRound,
} from 'lucide-angular';

import { SesionService } from '../nucleo/sesion.service';
import { Avatar } from '../nucleo/ui/avatar';

/** Tarjeta del usuario que despliega sus opciones, entre ellas cerrar la sesión. */
@Component({
  selector: 'app-menu-usuario',
  imports: [Avatar, RouterLink, LucideAngularModule],
  host: {
    class: 'relative block',
    '(document:click)': 'alPulsarFuera($event)',
    '(document:keydown.escape)': 'abierto.set(false)',
  },
  template: `
    @if (abierto()) {
      <div
        role="menu"
        class="absolute z-30 w-60 animate-aparecer rounded-2xl border border-borde bg-superficie p-1.5 shadow-xl shadow-tinta/10"
        [class]="compacto() ? 'top-full right-0 mt-2' : 'right-0 bottom-full left-0 mb-2 w-auto'"
      >
        <div class="border-b border-borde px-3 pt-2 pb-3">
          <p class="truncate text-sm font-semibold">{{ usuario()?.nombre }}</p>
          <p class="mt-0.5 truncate text-[13px] text-tinta-tenue" [title]="usuario()?.email">
            {{ usuario()?.email }}
          </p>
        </div>
        <div class="pt-1.5">
          <a
            routerLink="/privacidad"
            role="menuitem"
            class="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-tinta-suave transition hover:bg-fondo hover:text-tinta"
            (click)="abierto.set(false)"
          >
            <lucide-icon [img]="iconos.ShieldCheck" [size]="17" />
            Privacidad
          </a>
          <a
            routerLink="/cuenta"
            role="menuitem"
            class="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-tinta-suave transition hover:bg-fondo hover:text-tinta"
            (click)="abierto.set(false)"
          >
            <lucide-icon [img]="iconos.UserRound" [size]="17" />
            Mi cuenta
          </a>
          <button
            type="button"
            role="menuitem"
            class="group flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-tinta-suave transition hover:bg-fondo hover:text-tinta focus-visible:bg-fondo focus-visible:text-tinta focus-visible:outline-none"
            (click)="salir()"
          >
            <lucide-icon [img]="iconos.Power" [size]="17" />
            Cerrar sesión
            <span
              class="ml-auto -translate-x-1.5 opacity-0 transition duration-200 group-hover:translate-x-0 group-hover:opacity-100 group-focus-visible:translate-x-0 group-focus-visible:opacity-100"
              aria-hidden="true"
            >
              <lucide-icon [img]="iconos.ArrowRight" [size]="16" />
            </span>
          </button>
        </div>
      </div>
    }

    <button
      type="button"
      class="flex w-full items-center gap-3 rounded-xl text-left transition hover:bg-fondo focus-visible:ring-4 focus-visible:ring-acento/25 focus-visible:outline-none"
      [class]="compacto() ? 'p-0.5' : 'p-2'"
      aria-haspopup="menu"
      [attr.aria-expanded]="abierto()"
      [attr.aria-label]="'Menú de ' + usuario()?.nombre"
      (click)="abierto.set(!abierto())"
    >
      <app-avatar [nombre]="usuario()?.nombre ?? ''" [avatar]="usuario()?.avatar" />
      @if (!compacto()) {
        <span class="min-w-0 flex-1">
          <span class="block truncate text-sm font-semibold">{{ usuario()?.nombre }}</span>
          <span class="block truncate text-xs text-tinta-tenue">{{ usuario()?.email }}</span>
        </span>
        <lucide-icon [img]="iconos.ChevronsUpDown" [size]="16" class="shrink-0 text-tinta-tenue" />
      }
    </button>
  `,
})
export class MenuUsuario {
  /** Solo el avatar, con el menú hacia abajo (cabecera en móvil). */
  readonly compacto = input(false);

  private readonly sesion = inject(SesionService);
  private readonly router = inject(Router);
  private readonly elemento = inject<ElementRef<HTMLElement>>(ElementRef);

  protected readonly iconos = { ArrowRight, ChevronsUpDown, Power, ShieldCheck, UserRound };
  protected readonly abierto = signal(false);
  protected readonly usuario = this.sesion.usuario;

  protected alPulsarFuera(evento: Event): void {
    if (!this.elemento.nativeElement.contains(evento.target as Node)) this.abierto.set(false);
  }

  protected salir(): void {
    this.sesion.salir().subscribe(() => this.router.navigateByUrl('/entrar'));
  }
}
