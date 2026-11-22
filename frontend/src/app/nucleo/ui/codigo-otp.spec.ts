// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { TestBed } from '@angular/core/testing';

import { CodigoOtp } from './codigo-otp';

describe('CodigoOtp', () => {
  function crear() {
    const fixture = TestBed.createComponent(CodigoOtp);
    fixture.detectChanges();
    const casillas = Array.from(
      (fixture.nativeElement as HTMLElement).querySelectorAll('input'),
    ) as HTMLInputElement[];
    const emitidos: string[] = [];
    fixture.componentInstance.completo.subscribe((c) => emitidos.push(c));
    return { fixture, casillas, emitidos };
  }

  it('tiene seis casillas y emite el código al escribir la última cifra', () => {
    const { casillas, emitidos } = crear();
    expect(casillas.length).toBe(6);
    '481902'.split('').forEach((c, i) => {
      casillas[i].value = c;
      casillas[i].dispatchEvent(new Event('input'));
    });
    expect(emitidos).toEqual(['481902']);
  });

  it('ignora lo que no son cifras', () => {
    const { casillas } = crear();
    casillas[0].value = 'a';
    casillas[0].dispatchEvent(new Event('input'));
    expect(casillas[0].value).toBe('');
  });

  it('acepta pegar el código completo', () => {
    const { casillas, emitidos } = crear();
    const evento = new Event('paste') as ClipboardEvent;
    Object.defineProperty(evento, 'clipboardData', { value: { getData: () => ' 481 902 ' } });
    casillas[0].dispatchEvent(evento);
    expect(emitidos).toEqual(['481902']);
  });
});
