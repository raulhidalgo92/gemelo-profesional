// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { Component, inject, input, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { LoaderCircle, LucideAngularModule } from 'lucide-angular';

import { codigoDeError, mensajeDeError, SesionService } from '../../nucleo/sesion.service';
import { NuevaContrasena } from '../../nucleo/ui/nueva-contrasena';
import { entrarTrasCambiar } from './recuperar-codigo';

const MIN_CLAVE = 10;

/**
 * Nueva contraseña desde el botón del correo. El token se envía por POST al guardar: algunos
 * filtros de correo abren los enlaces para analizarlos y no deben poder usarlo.
 */
@Component({
  selector: 'app-restablecer',
  imports: [LucideAngularModule, NuevaContrasena, RouterLink],
  template: `
    <div class="mb-8">
      <h1 class="titulo-acceso">Elige tu nueva contraseña</h1>
      <p class="mt-2 text-tinta-suave">Al guardarla entrarás directamente en tu gemelo.</p>
    </div>

    <form (submit)="$event.preventDefault(); cambiar()" novalidate class="space-y-6">
      <div>
        <app-nueva-contrasena [(valor)]="contrasena" />
      </div>
      @if (error()) {
        <p class="rounded-xl bg-error/8 px-4 py-3 text-sm text-error" role="alert">
          {{ error() }}
          @if (caducado()) {
            <a routerLink="/recuperar" class="enlace ml-1">Pedir otro código</a>
          }
        </p>
      }
      <button
        type="submit"
        class="boton-primario w-full"
        [disabled]="contrasena().length < minClave || enviando()"
      >
        @if (enviando()) {
          <lucide-icon [img]="iconos.LoaderCircle" [size]="18" class="animate-spin" />
        }
        Cambiar contraseña
      </button>
    </form>
  `,
})
export class RestablecerPagina {
  /** De la ruta: /restablecer?token=… */
  readonly token = input('');
  private readonly sesion = inject(SesionService);
  private readonly router = inject(Router);

  protected readonly iconos = { LoaderCircle };
  protected readonly minClave = MIN_CLAVE;
  protected readonly contrasena = signal('');
  protected readonly enviando = signal(false);
  protected readonly error = signal('');
  protected readonly caducado = signal(false);

  protected cambiar(): void {
    if (this.contrasena().length < MIN_CLAVE) return;
    this.enviando.set(true);
    this.error.set('');
    this.sesion.restablecer({ token: this.token(), contrasena: this.contrasena() }).subscribe({
      next: (u) => entrarTrasCambiar(this.router, u),
      error: (e) => {
        this.enviando.set(false);
        this.caducado.set(codigoDeError(e) === 'enlace_no_valido');
        this.error.set(mensajeDeError(e));
      },
    });
  }
}
