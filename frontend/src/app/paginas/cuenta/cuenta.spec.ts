// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { HttpErrorResponse } from '@angular/common/http';
import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { of, throwError } from 'rxjs';
import { vi } from 'vitest';

import { Cuenta, SesionService } from '../../nucleo/sesion.service';
import { CuentaPagina } from './cuenta';

const CUENTA: Cuenta = {
  nombre: 'Laura',
  email: 'laura@ejemplo.com',
  verificada_en: '2026-11-20T10:00:00Z',
  consentimiento_en: '2026-11-20T10:00:00Z',
  consentimiento_version: '2026-11',
  otras_sesiones: 2,
};

function crear() {
  const sesion = {
    usuario: signal({
      nombre: 'Laura',
      email: CUENTA.email,
      avatar: null as string | null,
      bienvenida_pendiente: false,
    }),
    cuenta: () => of(CUENTA),
    cambiarNombre: vi.fn(() => of({})),
    cambiarAvatar: vi.fn(() => of({})),
    cambiarContrasena: vi.fn(() => of(undefined)),
    cerrarOtrasSesiones: vi.fn(() => of(undefined)),
    darDeBaja: vi.fn(() => of(undefined)),
  };
  TestBed.configureTestingModule({
    imports: [CuentaPagina],
    providers: [provideRouter([]), { provide: SesionService, useValue: sesion }],
  });
  const fixture = TestBed.createComponent(CuentaPagina);
  fixture.detectChanges();
  const el = fixture.nativeElement as HTMLElement;
  const boton = (texto: string) =>
    [...el.querySelectorAll('button')].find((b) => b.textContent!.trim() === texto)!;
  const escribir = (selector: string, valor: string) => {
    const input = el.querySelector<HTMLInputElement>(selector)!;
    input.value = valor;
    input.dispatchEvent(new Event('input'));
  };
  const pulsar = (texto: string) => {
    boton(texto).click();
    fixture.detectChanges();
  };
  return { fixture, el, sesion, boton, escribir, pulsar };
}

// jsdom no implementa <dialog>: basta con que se pueda abrir y cerrar
beforeAll(() => {
  HTMLDialogElement.prototype.showModal = function () {
    this.setAttribute('open', '');
  };
  HTMLDialogElement.prototype.close = function () {
    this.removeAttribute('open');
  };
});

describe('CuentaPagina', () => {
  it('muestra los datos, el consentimiento y las sesiones', () => {
    const { el } = crear();
    const texto = el.textContent!;
    expect(texto).toContain('laura@ejemplo.com');
    expect(el.querySelector('[aria-label="Correo verificado"]')).toBeTruthy();
    expect(texto).toContain('Aceptado el 20 de noviembre de 2026 · versión 2026-11');
    expect(texto).toContain('2 sesiones en otros dispositivos');
    expect(el.querySelector('a[href="/api/cuenta/exportar"]')).toBeTruthy();
  });

  it('cambia el nombre en su sitio y cierra las demás sesiones', () => {
    const { fixture, el, sesion, escribir, pulsar, boton } = crear();
    pulsar('Editar nombre');
    expect(boton('Guardar').disabled).toBe(true); // sin cambios
    escribir('[aria-label="Tu nombre"]', '  Laura María ');
    fixture.detectChanges();
    pulsar('Guardar');
    expect(sesion.cambiarNombre).toHaveBeenCalledWith('Laura María');
    expect(el.textContent).toContain('Nombre actualizado');

    pulsar('Cerrar sesiones');
    expect(sesion.cerrarOtrasSesiones).toHaveBeenCalled();
    expect(el.textContent).toContain('Solo tienes abierta esta sesión');
    expect(boton('Cerrar sesiones').disabled).toBe(true);
  });

  it('valida la nueva contraseña antes de enviarla', () => {
    const { el, sesion, escribir, pulsar } = crear();
    pulsar('Cambiar contraseña');
    escribir('input[formcontrolname=actual]', 'una-clave-larga');
    escribir('input[formcontrolname=nueva]', 'corta');
    pulsar('Guardar');
    expect(el.textContent).toContain('al menos 10 caracteres');
    expect(sesion.cambiarContrasena).not.toHaveBeenCalled();
  });

  it('eliminar abre un diálogo con lo que se pierde y vuelve a la entrada', () => {
    const { fixture, el, sesion, escribir, pulsar, boton } = crear();
    const navegar = vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true);
    pulsar('Eliminar cuenta');
    expect(el.querySelector('dialog')!.hasAttribute('open')).toBe(true);
    expect(el.textContent).toContain('Tu gemelo: trayectoria, competencias y evidencias');
    expect(boton('Eliminar definitivamente').disabled).toBe(true);
    escribir('#confirmar-baja', 'una-clave-larga');
    fixture.detectChanges();
    pulsar('Eliminar definitivamente');
    expect(sesion.darDeBaja).toHaveBeenCalledWith('una-clave-larga');
    expect(navegar).toHaveBeenCalledWith('/entrar', {
      state: { aviso: 'Hemos eliminado tu cuenta y todos tus datos.' },
    });
  });

  it('con la contraseña equivocada no habla de correo', () => {
    const { el, sesion, escribir, pulsar, fixture } = crear();
    const error = new HttpErrorResponse({
      status: 400,
      error: { detail: 'contrasena_incorrecta' },
    });
    sesion.darDeBaja.mockReturnValue(throwError(() => error));
    pulsar('Eliminar cuenta');
    escribir('#confirmar-baja', 'no-es-la-clave');
    fixture.detectChanges();
    pulsar('Eliminar definitivamente');
    expect(el.textContent).toContain('La contraseña no es correcta.');
    expect(el.textContent).not.toContain('correo o la contraseña');
  });

  it('elige un avatar de la colección y se guarda al momento', () => {
    const { fixture, el, sesion } = crear();
    el.querySelector<HTMLButtonElement>('[aria-label="Cambiar avatar"]')!.click();
    fixture.detectChanges();
    const opciones = el.querySelectorAll<HTMLButtonElement>('.opcion');
    expect(opciones).toHaveLength(9);
    expect(opciones[0].getAttribute('aria-pressed')).toBe('true'); // la inicial
    el.querySelector<HTMLButtonElement>('[aria-label="Luna"]')!.click();
    fixture.detectChanges();
    expect(sesion.cambiarAvatar).toHaveBeenCalledWith('luna');
    expect(el.textContent).toContain('Avatar actualizado');
  });

  it('el nombre vacío no se guarda y Esc cancela', () => {
    const { fixture, el, sesion, escribir, pulsar } = crear();
    pulsar('Editar nombre');
    escribir('[aria-label="Tu nombre"]', '   ');
    const campo = el.querySelector<HTMLInputElement>('[aria-label="Tu nombre"]')!;
    campo.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }));
    fixture.detectChanges();
    expect(el.textContent).toContain('El nombre no puede estar vacío.');
    expect(sesion.cambiarNombre).not.toHaveBeenCalled();
    campo.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
    fixture.detectChanges();
    expect(el.querySelector('[aria-label="Tu nombre"]')).toBeNull();
    expect(el.textContent).toContain('laura@ejemplo.com');
  });

  it('solo se edita una cosa cada vez', () => {
    const { el, pulsar } = crear();
    pulsar('Cambiar contraseña');
    expect(el.querySelector('input[formcontrolname=actual]')).toBeTruthy();
    pulsar('Editar nombre');
    expect(el.querySelector('[aria-label="Tu nombre"]')).toBeTruthy();
    expect(el.querySelector('input[formcontrolname=actual]')).toBeNull();
    pulsar('Cambiar contraseña');
    expect(el.querySelector('[aria-label="Tu nombre"]')).toBeNull();
  });
});
