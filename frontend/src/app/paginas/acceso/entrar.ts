// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { Component, inject, input, signal } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { Eye, EyeOff, LoaderCircle, LucideAngularModule } from 'lucide-angular';

import { SesionService, codigoDeError, mensajeDeError } from '../../nucleo/sesion.service';

@Component({
  selector: 'app-entrar',
  imports: [ReactiveFormsModule, RouterLink, LucideAngularModule],
  template: `
    <div class="mb-8">
      <h1 class="titulo-acceso">¿Tu siguiente paso?</h1>
      <p class="mt-2 text-tinta-suave">Entra y deja que tu gemelo te ayude a descubrirlo.</p>
    </div>

    <form [formGroup]="form" (ngSubmit)="enviar()" novalidate class="space-y-5">
      <div>
        <label for="email" class="etiqueta-campo">Correo electrónico</label>
        <input id="email" type="email" formControlName="email" class="campo" autocomplete="email" />
      </div>
      <div>
        <label for="contrasena" class="etiqueta-campo">Contraseña</label>
        <div class="relative">
          <input
            id="contrasena"
            [type]="verClave() ? 'text' : 'password'"
            formControlName="contrasena"
            class="campo pr-11"
            autocomplete="current-password"
          />
          <button
            type="button"
            (click)="verClave.set(!verClave())"
            class="absolute inset-y-0 right-0 grid w-11 place-items-center text-tinta-tenue transition hover:text-tinta"
            [attr.aria-label]="verClave() ? 'Ocultar contraseña' : 'Mostrar contraseña'"
          >
            <lucide-icon [img]="verClave() ? iconos.EyeOff : iconos.Eye" [size]="18" />
          </button>
        </div>
      </div>

      @if (error()) {
        <p class="rounded-xl bg-error/8 px-4 py-3 text-sm text-error" role="alert">{{ error() }}</p>
      }

      <button type="submit" class="boton-primario w-full" [disabled]="enviando()">
        @if (enviando()) {
          <lucide-icon [img]="iconos.LoaderCircle" [size]="18" class="animate-spin" />
        }
        Entrar
      </button>
    </form>

    <p class="mt-8 text-center text-sm text-tinta-suave">
      ¿Aún no tienes cuenta? <a routerLink="/registro" class="enlace">Créala en un minuto</a>
    </p>
  `,
})
export class EntrarPagina {
  /** Ruta a la que volver tras entrar (la pone la guarda de sesión). */
  readonly volver = input('');
  private readonly sesion = inject(SesionService);
  private readonly router = inject(Router);

  protected readonly iconos = { Eye, EyeOff, LoaderCircle };
  protected readonly enviando = signal(false);
  protected readonly error = signal('');
  protected readonly verClave = signal(false);
  protected readonly form = inject(NonNullableFormBuilder).group({
    email: ['', [Validators.required, Validators.email]],
    contrasena: ['', Validators.required],
  });

  protected enviar(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      this.error.set('Escribe tu correo y tu contraseña.');
      return;
    }
    const { email, contrasena } = this.form.getRawValue();
    this.enviando.set(true);
    this.error.set('');
    this.sesion.entrar(email, contrasena).subscribe({
      next: (u) => {
        const destino = u.bienvenida_pendiente ? '/bienvenida' : this.volver() || '/gemelo';
        this.router.navigateByUrl(destino.startsWith('/') ? destino : '/gemelo');
      },
      error: (e) => {
        this.enviando.set(false);
        if (codigoDeError(e) === 'cuenta_no_verificada') {
          // Se envía un código nuevo y se lleva al usuario a escribirlo
          this.sesion.recordarEmail(email);
          this.sesion.reenviar(email).subscribe({ error: () => undefined });
          this.router.navigateByUrl('/registro/codigo');
          return;
        }
        this.error.set(mensajeDeError(e));
      },
    });
  }
}
