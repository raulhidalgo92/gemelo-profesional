// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

import { Logo } from '../../nucleo/ui/logo';

/** Política de privacidad (versión 2026-11, la que se registra al aceptar el consentimiento). */
@Component({
  selector: 'app-privacidad',
  imports: [RouterLink, Logo],
  template: `
    <div class="mx-auto max-w-2xl px-6 py-12">
      <a routerLink="/registro"><app-logo /></a>
      <h1 class="mt-10 text-3xl font-semibold tracking-tight">Política de privacidad</h1>
      <p class="mt-2 text-sm text-tinta-tenue">Versión 2026-11</p>

      <div
        class="mt-8 space-y-6 leading-relaxed text-tinta-suave [&_h2]:mb-2 [&_h2]:text-lg [&_h2]:font-semibold [&_h2]:text-tinta"
      >
        <section>
          <h2>Quién trata tus datos y para qué</h2>
          <p>
            Esta aplicación es un prototipo desarrollado como Trabajo Fin de Grado en la Universidad
            Internacional de La Rioja. Tus datos se usan únicamente para crear tu gemelo profesional
            y ofrecerte recomendaciones de empleo, formación y trayectoria. La base legal es tu
            consentimiento, que puedes retirar en cualquier momento.
          </p>
        </section>
        <section>
          <h2>Qué datos guardamos</h2>
          <p>
            Tu nombre, tu correo, tu contraseña cifrada, la fecha y versión de este consentimiento,
            y las competencias y la experiencia que extraemos de tu currículum. El archivo del CV se
            elimina nada más analizarlo. No guardamos audio ni vídeo de las entrevistas simuladas:
            la voz se transcribe y se descarta.
          </p>
        </section>
        <section>
          <h2>Inteligencia artificial</h2>
          <p>
            Para analizar tu CV usamos modelos de lenguaje que se ejecutan en servidores de la Unión
            Europea. Antes de enviarles el texto, sustituimos tus datos identificativos (nombre,
            correo, teléfono, documento de identidad) por marcadores.
          </p>
        </section>
        <section>
          <h2>Tus derechos</h2>
          <p>
            Puedes acceder a tus datos, corregirlos o borrar tu cuenta con todos sus datos desde la
            propia aplicación. También puedes reclamar ante la Agencia Española de Protección de
            Datos.
          </p>
        </section>
      </div>
    </div>
  `,
})
export class PrivacidadPagina {}
