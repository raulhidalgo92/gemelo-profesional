// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { fortaleza } from './fortaleza';

describe('fortaleza de la contraseña', () => {
  it('sin texto no se muestra y por debajo de 10 caracteres es muy débil', () => {
    expect(fortaleza('')).toBe(-1);
    expect(fortaleza('Ab1!')).toBe(0);
  });

  it('sube con la longitud y la variedad de caracteres', () => {
    expect(fortaleza('abcdefghij')).toBe(1);
    expect(fortaleza('abcdefghiJ1')).toBe(3);
    expect(fortaleza('una frase larga Con 1 símbolo!')).toBe(4);
  });
});
