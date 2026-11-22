// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { Component, OnInit, inject, input, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { CircleAlert, LoaderCircle, LucideAngularModule } from 'lucide-angular';

import { SesionService, mensajeDeError } from '../../nucleo/sesion.service';

/**
 * Activación con el botón del correo. El token se envía por POST: algunos filtros de correo
 * abren los enlaces para analizarlos y no deben activar la cuenta por su cuenta.
 */
@Component({
  selector: 'app-verificar-enlace',
  imports: [RouterLink, LucideAngularModule],
  template: `
    @if (error()) {
      <span class="mb-6 grid size-12 place-items-center rounded-2xl bg-error/8 text-error">
        <lucide-icon [img]="iconos.CircleAlert" [size]="22" />
      </span>
      <h1 class="text-[28px] leading-tight font-semibold tracking-tight">
        No hemos podido activarla
      </h1>
      <p class="mt-2 text-tinta-suave">{{ error() }}</p>
      <div class="mt-8 flex gap-3">
        <a routerLink="/entrar" class="boton-primario">Iniciar sesión</a>
        <a routerLink="/registro" class="boton-secundario">Registrarme de nuevo</a>
      </div>
    } @else {
      <div class="flex items-center gap-3 text-tinta-suave">
        <lucide-icon [img]="iconos.LoaderCircle" [size]="20" class="animate-spin" />
        Activando tu cuenta…
      </div>
    }
  `,
})
export class VerificarEnlacePagina implements OnInit {
  readonly token = input('');
  private readonly sesion = inject(SesionService);
  private readonly router = inject(Router);
  protected readonly iconos = { CircleAlert, LoaderCircle };
  protected readonly error = signal('');

  ngOnInit(): void {
    this.sesion.verificarEnlace(this.token()).subscribe({
      next: () => this.router.navigateByUrl('/bienvenida', { replaceUrl: true }),
      error: async (e) => {
        // Si el enlace se abrió dos veces, la otra petición ya habrá abierto la sesión
        this.sesion.usuario.set(undefined);
        if (await this.sesion.cargar()) {
          this.router.navigateByUrl('/bienvenida', { replaceUrl: true });
        } else {
          this.error.set(mensajeDeError(e));
        }
      },
    });
  }
}
