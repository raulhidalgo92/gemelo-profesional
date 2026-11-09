// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { DecimalPipe } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { catchError, debounceTime, distinctUntilChanged, filter, of, Subject, switchMap } from 'rxjs';

import { ApiService, Competencia } from '../../nucleo/api.service';

@Component({
  selector: 'app-gemelo',
  imports: [DecimalPipe],
  templateUrl: './gemelo.html',
  styleUrl: './gemelo.scss',
})
export class GemeloPagina {
  private readonly api = inject(ApiService);

  protected readonly salud = toSignal(this.api.salud().pipe(catchError(() => of(null))), {
    initialValue: undefined,
  });
  protected readonly mercado = toSignal(
    this.api.resumenMercado().pipe(catchError(() => of(null))),
    { initialValue: undefined },
  );

  private readonly busqueda$ = new Subject<string>();
  protected readonly texto = signal('');
  protected readonly resultados = toSignal(
    this.busqueda$.pipe(
      debounceTime(250),
      distinctUntilChanged(),
      filter((q) => q.length >= 2),
      switchMap((q) => this.api.buscarCompetencias(q).pipe(catchError(() => of([])))),
    ),
    { initialValue: [] as Competencia[] },
  );

  protected buscar(valor: string): void {
    this.texto.set(valor);
    this.busqueda$.next(valor.trim());
  }
}
