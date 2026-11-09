// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { App } from './app';

describe('App', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [provideRouter([])],
    }).compileComponents();
  });

  it('muestra los cinco apartados del menú', () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    const enlaces = (fixture.nativeElement as HTMLElement).querySelectorAll('nav a');
    expect(enlaces.length).toBe(5);
  });
});
