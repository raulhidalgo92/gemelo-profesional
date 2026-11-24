// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { Component, computed, DestroyRef, inject, OnInit, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { LoaderCircle, LucideAngularModule } from 'lucide-angular';

import { mensajeDeError, SesionService, Usuario } from '../../nucleo/sesion.service';
import { CodigoOtp } from '../../nucleo/ui/codigo-otp';
import { NuevaContrasena } from '../../nucleo/ui/nueva-contrasena';

const ESPERA_REENVIO = 60;
const MIN_CLAVE = 10;

/** Tras cambiar la contraseña se entra directamente, con un aviso en el panel. */
export function entrarTrasCambiar(router: Router, usuario: Usuario): void {
  router.navigateByUrl(usuario.bienvenida_pendiente ? '/bienvenida' : '/gemelo', {
    replaceUrl: true,
    state: { aviso: 'Contraseña cambiada' },
  });
}

/** Contraseña olvidada, paso 2: el código del correo y la contraseña nueva. */
@Component({
  selector: 'app-recuperar-codigo',
  imports: [CodigoOtp, LucideAngularModule, NuevaContrasena, RouterLink],
  template: `
    <div class="mb-8">
      <h1 class="titulo-acceso">Revisa tu correo</h1>
      <p class="mt-2 text-tinta-suave">
        Si hay una cuenta con
        <span class="font-medium break-all text-tinta">{{ email() }}</span
        >, te hemos enviado un código de 6 cifras. Escríbelo y elige tu nueva contraseña.
      </p>
    </div>

    <form (submit)="$event.preventDefault(); cambiar()" novalidate class="space-y-6">
      <div>
        <app-codigo-otp
          [deshabilitado]="enviando()"
          [error]="fallo()"
          (completo)="codigo.set($event)"
        />
      </div>
      <div>
        <app-nueva-contrasena [(valor)]="contrasena" />
      </div>
      @if (error()) {
        <p class="rounded-xl bg-error/8 px-4 py-3 text-sm text-error" role="alert">{{ error() }}</p>
      } @else if (aviso()) {
        <p class="text-sm text-ok" role="status">{{ aviso() }}</p>
      }
      <button type="submit" class="boton-primario w-full" [disabled]="!listo() || enviando()">
        @if (enviando()) {
          <lucide-icon [img]="iconos.LoaderCircle" [size]="18" class="animate-spin" />
        }
        Cambiar contraseña
      </button>
    </form>

    <div class="mt-8 flex flex-wrap items-center justify-between gap-3 text-sm text-tinta-suave">
      @if (segundos() > 0) {
        <span>Puedes pedir otro código en {{ segundos() }} s</span>
      } @else {
        <button type="button" class="enlace" (click)="reenviar()">Reenviar el código</button>
      }
      <a routerLink="/recuperar" class="boton-texto text-sm">Cambiar el correo</a>
    </div>

    <p
      class="mt-10 rounded-xl bg-superficie px-4 py-3 text-[13px] leading-relaxed text-tinta-tenue ring-1 ring-borde"
    >
      ¿No lo encuentras? Mira en la carpeta de spam o promociones. El código caduca en 15 minutos.
    </p>
  `,
})
export class RecuperarCodigoPagina implements OnInit {
  private readonly sesion = inject(SesionService);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);

  protected readonly iconos = { LoaderCircle };
  protected readonly email = this.sesion.emailPendiente;
  protected readonly codigo = signal('');
  protected readonly contrasena = signal('');
  protected readonly listo = computed(
    () => this.codigo().length === 6 && this.contrasena().length >= MIN_CLAVE,
  );
  protected readonly enviando = signal(false);
  protected readonly fallo = signal(false);
  protected readonly error = signal('');
  protected readonly aviso = signal('');
  protected readonly segundos = signal(ESPERA_REENVIO);

  ngOnInit(): void {
    if (!this.email()) {
      this.router.navigateByUrl('/recuperar');
      return;
    }
    const temporizador = setInterval(() => this.segundos.update((s) => Math.max(0, s - 1)), 1000);
    this.destroyRef.onDestroy(() => clearInterval(temporizador));
  }

  protected cambiar(): void {
    if (!this.listo()) return;
    this.enviando.set(true);
    this.fallo.set(false);
    this.error.set('');
    this.sesion
      .restablecer({ email: this.email(), codigo: this.codigo(), contrasena: this.contrasena() })
      .subscribe({
        next: (u) => entrarTrasCambiar(this.router, u),
        error: (e) => {
          this.enviando.set(false);
          this.error.set(mensajeDeError(e));
          // Se fuerza el cambio para que vuelva a temblar aunque ya hubiera fallado antes
          queueMicrotask(() => this.fallo.set(true));
        },
      });
  }

  protected reenviar(): void {
    this.sesion.recuperar(this.email()).subscribe({
      next: () => {
        this.segundos.set(ESPERA_REENVIO);
        this.error.set('');
        this.aviso.set('Si la cuenta existe, te hemos enviado un código nuevo.');
      },
      error: (e) => this.error.set(mensajeDeError(e)),
    });
  }
}
