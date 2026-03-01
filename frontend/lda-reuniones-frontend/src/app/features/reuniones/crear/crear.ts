import { CommonModule } from '@angular/common';
import { Component, computed, signal, DestroyRef, inject } from '@angular/core';
import {
  AbstractControl,
  FormBuilder,
  FormGroup,
  ReactiveFormsModule,
  ValidationErrors,
  Validators,
} from '@angular/forms';
import { Router } from '@angular/router';
import { CatalogosService } from '../../../core/api/catalogos.service';
import { ReunionesService } from '../../../core/api/reuniones.service';
import { CatalogoItem } from '../../../core/models/catalogo.model';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

type SelectItem = { id: number; codigo: string; nombre_mostrado: string };

@Component({
  selector: 'app-crear',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './crear.html',
  styleUrl: './crear.scss',
})
export default class CrearComponent {
  private destroyRef = inject(DestroyRef);

  // catálogos base
  modalidades = signal<CatalogoItem[]>([]);
  sedes = signal<any[]>([]);
  tiposDocumento = signal<CatalogoItem[]>([]);

  // ✅ clasificación (100% BD)
  procesos = signal<SelectItem[]>([]);
  subprocesos = signal<SelectItem[]>([]);
  lineasTrabajo = signal<SelectItem[]>([]);

  // UI
  loading = signal(false);
  errorMsg = signal<string | null>(null);

  minDate = (() => {
    const d = new Date();
    // hoy SIN hora (evita que “hoy” quede inválido)
    return new Date(d.getFullYear(), d.getMonth(), d.getDate()).toISOString().slice(0, 10);
  })();
  readonly emailDomain = '@almamater.hospital';

  form!: FormGroup;

  // para label dinámico
  tipoDocumentoSel = signal<string>('');
  nombreLabel = computed(() => {
    const v = this.tipoDocumentoSel();
    return v === 'DESPLIEGUE' ? 'Nombre de los documentos' : 'Nombre de la reunión';
  });

  // ✅ Regex
  private readonly nombreRegex = /^[A-Za-zÁÉÍÓÚáéíóúÑñÜü\s]+$/;
  private readonly soloNumerosRegex = /^\d+$/;
  private readonly emailLocalRegex = /^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+$/;

  constructor(
    private fb: FormBuilder,
    private catalogos: CatalogosService,
    private reuniones: ReunionesService,
    private router: Router
  ) {
    this.form = this.fb.group(
      {
        tipo_documento: ['', Validators.required],

        // (ya lo volviste textarea en el HTML; aquí solo validación)
        nombre_evento: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(4000)]],

        fecha_evento: ['', Validators.required],
        hora_inicio: ['', Validators.required],
        hora_fin: ['', Validators.required],

        modalidad: ['', Validators.required],
        sede: ['', Validators.required],

        lugar_texto: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(200)]],

        // ✅ Clasificación (IDs, no texto)
        proceso_id: [null, Validators.required],
        subproceso_id: [{ value: null, disabled: true }],     // opcional
        linea_trabajo_id: [{ value: null, disabled: true }],  // opcional

        anfitrion_nombre: [
          '',
          [
            Validators.required,
            Validators.minLength(3),
            Validators.maxLength(200),
            Validators.pattern(this.nombreRegex),
          ],
        ],

        anfitrion_identificacion: [
          '',
          [
            Validators.required,
            Validators.minLength(6),
            Validators.maxLength(30),
            Validators.pattern(this.soloNumerosRegex),
          ],
        ],

        anfitrion_correo_local: [
          '',
          [
            Validators.required,
            Validators.minLength(1),
            Validators.maxLength(120),
            Validators.pattern(this.emailLocalRegex),
            this.noAtSymbolValidator,
          ],
        ],

        anfitrion_cargo: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(150)]],
      },
      { validators: [this.validarRangoHoras] }
    );
  }

  ngOnInit() {
    // catálogos base
    this.catalogos.modalidades().subscribe((x) => this.modalidades.set(x));
    this.catalogos.tiposDocumento().subscribe((x) => this.tiposDocumento.set(x));

    // ✅ procesos desde BD
    this.catalogos.procesos().subscribe({
      next: (x) => {
        const items: SelectItem[] = (x ?? []).map((p: any) => ({
          id: Number(p.id),
          codigo: String(p.codigo),
          nombre_mostrado: String(p.nombre_mostrado ?? p.nombre ?? p.codigo),
        }));
        this.procesos.set(items);
      },
      error: () => this.procesos.set([]),
    });

    // ✅ tipo_documento => label dinámico
    this.form.controls['tipo_documento'].valueChanges
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((v) => this.tipoDocumentoSel.set(v ?? ''));

    // ✅ sedes depende de modalidad
    this.form.controls['modalidad'].valueChanges
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((modalidadCodigo) => {
        this.form.controls['sede'].setValue('');
        if (!modalidadCodigo) {
          this.sedes.set([]);
          return;
        }
        this.catalogos.sedes(modalidadCodigo).subscribe((x) => this.sedes.set(x));
      });

    // ✅ Proceso -> cargar subprocesos desde BD
    this.form.controls['proceso_id'].valueChanges
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((idProceso) => {
        // reset subproceso / línea
        this.subprocesos.set([]);
        this.lineasTrabajo.set([]);

        this.form.controls['subproceso_id'].reset(null, { emitEvent: false });
        this.form.controls['linea_trabajo_id'].reset(null, { emitEvent: false });

        this.form.controls['subproceso_id'].disable({ emitEvent: false });
        this.form.controls['linea_trabajo_id'].disable({ emitEvent: false });

        if (!idProceso) return;

        this.catalogos.subprocesos(Number(idProceso)).subscribe({
          next: (x) => {
            const items: SelectItem[] = (x ?? []).map((sp: any) => ({
              id: Number(sp.id),
              codigo: String(sp.codigo),
              nombre_mostrado: String(sp.nombre_mostrado ?? sp.nombre ?? sp.codigo),
            }));
            this.subprocesos.set(items);

            // si hay subprocesos, habilita el combo (pero NO requerido)
            if (items.length > 0) {
              this.form.controls['subproceso_id'].enable({ emitEvent: false });
            }
          },
          error: () => this.subprocesos.set([]),
        });
      });

    // ✅ Subproceso -> cargar líneas desde BD
    this.form.controls['subproceso_id'].valueChanges
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((idSubproceso) => {
        // reset línea
        this.lineasTrabajo.set([]);
        this.form.controls['linea_trabajo_id'].reset(null, { emitEvent: false });
        this.form.controls['linea_trabajo_id'].disable({ emitEvent: false });

        if (!idSubproceso) return;

        this.catalogos.lineasTrabajo(Number(idSubproceso)).subscribe({
          next: (x) => {
            const items: SelectItem[] = (x ?? []).map((lt: any) => ({
              id: Number(lt.id),
              codigo: String(lt.codigo),
              nombre_mostrado: String(lt.nombre_mostrado ?? lt.nombre ?? lt.codigo),
            }));
            this.lineasTrabajo.set(items);

            if (items.length > 0) {
              this.form.controls['linea_trabajo_id'].enable({ emitEvent: false });
            }
          },
          error: () => this.lineasTrabajo.set([]),
        });
      });
  }

  // =========================
  // Validaciones y helpers
  // =========================
  private validarRangoHoras(group: AbstractControl): ValidationErrors | null {
    const ini = group.get('hora_inicio')?.value as string | null;
    const fin = group.get('hora_fin')?.value as string | null;
    if (!ini || !fin) return null;
    return ini < fin ? null : { rango_horas_invalido: true };
  }

  private noAtSymbolValidator(control: AbstractControl): ValidationErrors | null {
    const v = (control.value ?? '') as string;
    return v.includes('@') ? { contiene_arroba: true } : null;
  }

  private buildCorreoFinal(): string {
    const local = (this.form.controls['anfitrion_correo_local'].value ?? '').trim();
    const limpio = local.replace(/\s+/g, '').replace(/@/g, '');
    return `${limpio}${this.emailDomain}`;
  }

  private extractFastApiError(err: any): string {
    const detail = err?.error?.detail;
    if (Array.isArray(detail)) {
      return detail
        .map((d) => {
          const path = Array.isArray(d.loc) ? d.loc.join('.') : '';
          const msg = d.msg ?? 'Error de validación';
          return path ? `${path}: ${msg}` : msg;
        })
        .join(' | ');
    }
    if (typeof detail === 'string') return detail;
    if (detail && typeof detail === 'object') return JSON.stringify(detail);
    return 'Error creando la reunión.';
  }

  // =========================
  // Submit
  // =========================
  submit() {
    this.errorMsg.set(null);

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      if (this.form.errors?.['rango_horas_invalido']) {
        this.errorMsg.set('La hora fin debe ser mayor que la hora inicio.');
      }
      return;
    }

    const correoFinal = this.buildCorreoFinal();

    // incluye disabled
    const raw = this.form.getRawValue();

    const payload = {
      tipo_documento: raw.tipo_documento,
      nombre: raw.nombre_evento,
      fecha: raw.fecha_evento,
      hora_inicio: raw.hora_inicio,
      hora_fin: raw.hora_fin,
      modalidad: raw.modalidad,
      sede: raw.sede,
      lugar_texto: raw.lugar_texto,

      // ✅ ahora mandamos IDs (BD)
      proceso_id: raw.proceso_id,
      subproceso_id: raw.subproceso_id,
      linea_trabajo_id: raw.linea_trabajo_id,

      anfitrion: {
        nombre_completo: (raw.anfitrion_nombre ?? '').trim(),
        identificacion: (raw.anfitrion_identificacion ?? '').trim(),
        correo: correoFinal,
        cargo: (raw.anfitrion_cargo ?? '').trim(),
      },
    };

    this.loading.set(true);
    this.reuniones.crear(payload).subscribe({
      next: (res) => {
        this.loading.set(false);
        this.router.navigate(['/reuniones/confirmacion', res.codigo_reunion]);
      },
      error: (err) => {
        this.loading.set(false);
        this.errorMsg.set(this.extractFastApiError(err));
      },
    });
  }

  // =========================
  // Keypress validators
  // =========================
  soloLetras(event: KeyboardEvent) {
    const key = event.key;
    if (key === 'Backspace' || key === 'Tab' || key === 'Enter' || key === 'ArrowLeft' || key === 'ArrowRight' || key === 'Delete') return;
    const ok = /^[A-Za-zÁÉÍÓÚáéíóúÑñÜü\s]$/.test(key);
    if (!ok) event.preventDefault();
  }

  soloNumeros(event: KeyboardEvent) {
    const key = event.key;
    if (key === 'Backspace' || key === 'Tab' || key === 'Enter' || key === 'ArrowLeft' || key === 'ArrowRight' || key === 'Delete') return;
    const ok = /^\d$/.test(key);
    if (!ok) event.preventDefault();
  }
}
