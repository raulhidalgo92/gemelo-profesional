// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { DecimalPipe, PercentPipe } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { toObservable, toSignal } from '@angular/core/rxjs-interop';
import {
  catchError,
  debounceTime,
  distinctUntilChanged,
  map,
  of,
  startWith,
  switchMap,
} from 'rxjs';

import { ApiService, BusquedaCompetencias, ModoBusqueda } from '../../nucleo/api.service';

const TIPOS: Record<string, string> = { skill: 'capacidad', knowledge: 'conocimiento' };

@Component({
  selector: 'app-gemelo',
  imports: [DecimalPipe, PercentPipe],
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

  protected readonly texto = signal('');
  protected readonly modo = signal<ModoBusqueda>('semantico');

  private readonly consulta = computed(() => ({ q: this.texto().trim(), modo: this.modo() }));

  /** null = sin consulta; undefined = buscando */
  protected readonly busqueda = toSignal(
    toObservable(this.consulta).pipe(
      debounceTime(300),
      distinctUntilChanged((a, b) => a.q === b.q && a.modo === b.modo),
      switchMap(({ q, modo }) =>
        q.length < 2
          ? of(null)
          : this.api.buscarCompetencias(q, modo).pipe(
              map((r): BusquedaCompetencias | null | undefined => r),
              catchError(() => of(null)),
              startWith(undefined),
            ),
      ),
    ),
    { initialValue: null },
  );

  /** Aviso cuando se pidió búsqueda por significado y el servidor respondió por texto */
  protected readonly sinIa = computed(() => {
    const b = this.busqueda();
    return !!b && this.modo() === 'semantico' && b.modo === 'texto';
  });

  protected tipo(t: string | null): string {
    return (t && TIPOS[t]) ?? 'competencia';
  }
}
