// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { HttpErrorResponse } from '@angular/common/http';
import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { of, throwError } from 'rxjs';
import { vi } from 'vitest';

import { SesionService, Usuario } from '../../nucleo/sesion.service';
import { RecuperarCodigoPagina } from './recuperar-codigo';
import { RestablecerPagina } from './restablecer';

const USUARIO: Usuario = {
  nombre: 'Ana',
  email: 'ana@ejemplo.com',
  avatar: null,
  bienvenida_pendiente: false,
};

function preparar(restablecer = vi.fn(() => of(USUARIO))) {
  const sesion = {
    emailPendiente: signal('ana@ejemplo.com'),
    recuperar: vi.fn(() => of(undefined)),
    restablecer,
  };
  TestBed.configureTestingModule({
    providers: [provideRouter([]), { provide: SesionService, useValue: sesion }],
  });
  const navegar = vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true);
  return { sesion, navegar };
}

function escribir(el: HTMLElement, selector: string, valor: string) {
  const campo = el.querySelector<HTMLInputElement>(selector)!;
  campo.value = valor;
  campo.dispatchEvent(new Event('input'));
}

describe('Recuperar la contraseña', () => {
  it('con el código y una contraseña válida, entra directamente', () => {
    const { sesion, navegar } = preparar();
    const fixture = TestBed.createComponent(RecuperarCodigoPagina);
    fixture.detectChanges();
    const el = fixture.nativeElement as HTMLElement;
    const boton = el.querySelector<HTMLButtonElement>('button[type=submit]')!;
    expect(boton.disabled).toBe(true);

    el.querySelectorAll<HTMLInputElement>('app-codigo-otp input').forEach((c, i) => {
      c.value = String(i + 1);
      c.dispatchEvent(new Event('input'));
    });
    escribir(el, '#nueva-contrasena', 'corta');
    fixture.detectChanges();
    expect(boton.disabled).toBe(true); // menos de 10 caracteres

    escribir(el, '#nueva-contrasena', 'otra-clave-larga');
    fixture.detectChanges();
    boton.click();
    expect(sesion.restablecer).toHaveBeenCalledWith({
      email: 'ana@ejemplo.com',
      codigo: '123456',
      contrasena: 'otra-clave-larga',
    });
    expect(navegar).toHaveBeenCalledWith('/gemelo', {
      replaceUrl: true,
      state: { aviso: 'Contraseña cambiada' },
    });
  });

  it('desde el enlace caducado ofrece pedir otro código', () => {
    const error = new HttpErrorResponse({ status: 400, error: { detail: 'enlace_no_valido' } });
    const { navegar } = preparar(vi.fn(() => throwError(() => error)));
    const fixture = TestBed.createComponent(RestablecerPagina);
    fixture.componentRef.setInput('token', 'x'.repeat(30));
    fixture.detectChanges();
    const el = fixture.nativeElement as HTMLElement;
    escribir(el, '#nueva-contrasena', 'otra-clave-larga');
    fixture.detectChanges();
    el.querySelector<HTMLButtonElement>('button[type=submit]')!.click();
    fixture.detectChanges();
    expect(el.textContent).toContain('Pedir otro código');
    expect(navegar).not.toHaveBeenCalled();
  });
});
