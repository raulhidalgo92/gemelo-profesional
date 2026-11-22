// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { Component, DestroyRef, OnInit, computed, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { LoaderCircle, LucideAngularModule, MailCheck } from 'lucide-angular';

import { SesionService, codigoDeError, mensajeDeError } from '../../nucleo/sesion.service';
import { CodigoOtp } from '../../nucleo/ui/codigo-otp';

const ESPERA_REENVIO = 60;

/** Registro, paso 2: el código de 6 cifras que llega por correo. */
@Component({
  selector: 'app-verificar-codigo',
  imports: [CodigoOtp, RouterLink, LucideAngularModule],
  template: `
    <div class="mb-8">
      <span class="mb-6 grid size-12 place-items-center rounded-2xl bg-acento-suave text-acento">
        <lucide-icon [img]="iconos.MailCheck" [size]="22" />
      </span>
      <p class="mb-3 text-[13px] font-medium tracking-wide text-acento uppercase">Paso 2 de 2</p>
      <h1 class="text-[28px] leading-tight font-semibold tracking-tight">Revisa tu correo</h1>
      <p class="mt-2 text-tinta-suave">
        Te hemos enviado un código de 6 cifras a
        <span class="font-medium text-tinta">{{ email() }}</span
        >. También puedes pulsar el botón del correo.
      </p>
    </div>

    <app-codigo-otp
      [deshabilitado]="comprobando()"
      [error]="fallo()"
      (completo)="comprobar($event)"
    />

    <div class="mt-4 h-6 text-sm" aria-live="polite">
      @if (comprobando()) {
        <span class="inline-flex items-center gap-2 text-tinta-suave">
          <lucide-icon [img]="iconos.LoaderCircle" [size]="16" class="animate-spin" />
          Comprobando…
        </span>
      } @else if (mensaje()) {
        <span [class]="mensajeOk() ? 'text-ok' : 'text-error'">{{ mensaje() }}</span>
      }
    </div>

    <div class="mt-8 flex flex-wrap items-center justify-between gap-3 text-sm text-tinta-suave">
      @if (segundos() > 0) {
        <span>Puedes pedir otro código en {{ segundos() }} s</span>
      } @else {
        <button type="button" class="enlace" (click)="reenviar()">Reenviar el código</button>
      }
      <a routerLink="/registro" class="boton-texto text-sm">Cambiar el correo</a>
    </div>

    <p
      class="mt-10 rounded-xl bg-superficie px-4 py-3 text-[13px] leading-relaxed text-tinta-tenue ring-1 ring-borde"
    >
      ¿No lo encuentras? Mira en la carpeta de spam o promociones. El código caduca en 15 minutos.
    </p>
  `,
})
export class VerificarCodigoPagina implements OnInit {
  private readonly sesion = inject(SesionService);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);

  protected readonly iconos = { LoaderCircle, MailCheck };
  protected readonly email = this.sesion.emailPendiente;
  protected readonly comprobando = signal(false);
  protected readonly fallo = signal(false);
  protected readonly mensaje = signal('');
  protected readonly mensajeOk = signal(false);
  protected readonly segundos = signal(ESPERA_REENVIO);
  protected readonly puedeReenviar = computed(() => this.segundos() === 0);

  ngOnInit(): void {
    if (!this.email()) {
      this.router.navigateByUrl('/registro');
      return;
    }
    const temporizador = setInterval(() => this.segundos.update((s) => Math.max(0, s - 1)), 1000);
    this.destroyRef.onDestroy(() => clearInterval(temporizador));
  }

  protected comprobar(codigo: string): void {
    this.comprobando.set(true);
    this.fallo.set(false);
    this.mensaje.set('');
    this.sesion.verificarCodigo(this.email(), codigo).subscribe({
      next: () => this.router.navigateByUrl('/bienvenida'),
      error: (e) => {
        this.comprobando.set(false);
        this.mensajeOk.set(false);
        this.mensaje.set(mensajeDeError(e));
        // Se fuerza el cambio para que vuelva a temblar aunque ya hubiera fallado antes
        queueMicrotask(() => this.fallo.set(true));
      },
    });
  }

  protected reenviar(): void {
    this.sesion.reenviar(this.email()).subscribe({
      next: () => {
        this.segundos.set(ESPERA_REENVIO);
        this.mensajeOk.set(true);
        this.mensaje.set('Te hemos enviado un código nuevo.');
      },
      error: (e) => {
        this.mensajeOk.set(false);
        this.mensaje.set(mensajeDeError(e));
        if (codigoDeError(e) === 'espera') {
          const espera = Number(e.headers?.get('Retry-After')) || ESPERA_REENVIO;
          this.segundos.set(espera);
        }
      },
    });
  }
}
