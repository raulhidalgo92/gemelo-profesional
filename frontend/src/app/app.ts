// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

interface EnlaceMenu {
  ruta: string;
  icono: string;
  texto: string;
}

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {
  protected readonly menu: EnlaceMenu[] = [
    { ruta: '/gemelo', icono: '🧠', texto: 'Mi gemelo' },
    { ruta: '/futuro', icono: '🧭', texto: 'Mi futuro' },
    { ruta: '/empleo', icono: '🔎', texto: 'Empleo' },
    { ruta: '/formacion', icono: '📚', texto: 'Formarte' },
    { ruta: '/entrenador', icono: '🎤', texto: 'Entrenador' },
  ];
}
