// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { Location } from '@angular/common';
import { Component, computed, inject } from '@angular/core';
import { Router } from '@angular/router';
import { ArrowLeft, LucideAngularModule } from 'lucide-angular';

import { SesionService } from '../../nucleo/sesion.service';
import { Logo } from '../../nucleo/ui/logo';

/** Política de privacidad (versión 2026-11, la que se registra al aceptar el consentimiento). */
@Component({
  selector: 'app-privacidad',
  template: `
    <div class="pagina-estrecha">
      <header class="cabecera-pagina">
        <div>
          <h1 class="titulo-pagina">Política de privacidad</h1>
          <p class="subtitulo-pagina">Cómo tratamos tus datos y qué puedes hacer.</p>
        </div>
      </header>

      @for (s of secciones; track s.titulo) {
        <section class="apartado">
          <h2 class="apartado-titulo">{{ s.titulo }}</h2>
          <p class="apartado-contenido mt-2! text-[15px] leading-7 text-tinta-suave">
            {{ s.texto }}
          </p>
        </section>
      }
    </div>
  `,
})
export class PrivacidadPagina {
  protected readonly secciones = [
    {
      titulo: 'Quién trata tus datos y para qué',
      texto:
        'Esta aplicación es un prototipo desarrollado como Trabajo Fin de Grado en la Universidad Internacional de La Rioja. Tus datos se usan únicamente para crear tu gemelo profesional y ofrecerte recomendaciones de empleo, formación y trayectoria. La base legal es tu consentimiento, que puedes retirar en cualquier momento.',
    },
    {
      titulo: 'Qué datos guardamos',
      texto:
        'Tu nombre, tu correo, tu contraseña cifrada, la fecha y versión de este consentimiento, y las competencias y la experiencia que extraemos de tu currículum. El archivo del CV se elimina nada más analizarlo. No guardamos audio ni vídeo de las entrevistas simuladas: la voz se transcribe y se descarta.',
    },
    {
      titulo: 'Inteligencia artificial',
      texto:
        'Para analizar tu CV usamos modelos de lenguaje que se ejecutan en servidores de la Unión Europea. Antes de enviarles el texto, sustituimos tus datos identificativos (nombre, correo, teléfono, documento de identidad) por marcadores.',
    },
    {
      titulo: 'Tus derechos',
      texto:
        'Puedes acceder a tus datos, corregirlos o borrar tu cuenta con todos sus datos desde la propia aplicación. También puedes reclamar ante la Agencia Española de Protección de Datos.',
    },
  ];
}

/** La misma página sin menú lateral, para quien aún no ha entrado en la aplicación. */
@Component({
  selector: 'app-privacidad-publica',
  imports: [Logo, LucideAngularModule, PrivacidadPagina],
  template: `
    <div class="px-5 py-8 sm:px-10 sm:py-10">
      <header class="pagina-estrecha mb-12 flex items-center justify-between gap-4">
        <app-logo [tamano]="32" />
        <button type="button" class="boton-secundario h-10 px-4 text-sm" (click)="volver()">
          <lucide-icon [img]="iconoVolver" [size]="16" />
          Volver
        </button>
      </header>
      <app-privacidad />
    </div>
  `,
})
export class PrivacidadPublicaPagina {
  private readonly sesion = inject(SesionService);
  private readonly router = inject(Router);
  private readonly location = inject(Location);
  private readonly inicio = computed(() => (this.sesion.conSesion() ? '/bienvenida' : '/registro'));

  protected readonly iconoVolver = ArrowLeft;

  /** Vuelve a la pantalla anterior; si se abrió directamente, a la de inicio. */
  protected volver(): void {
    if (this.router.lastSuccessfulNavigation()?.previousNavigation) {
      this.location.back();
    } else {
      this.router.navigateByUrl(this.inicio());
    }
  }
}
