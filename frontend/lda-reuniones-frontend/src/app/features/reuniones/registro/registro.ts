import { CommonModule } from '@angular/common';
import { Component, DestroyRef, inject, signal, computed } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

import { CatalogosService } from '../../../core/api/catalogos.service';
import { ReunionesService } from '../../../core/api/reuniones.service';
import { CatalogoItem } from '../../../core/models/catalogo.model';

type CatalogoLite = { id: number; codigo: string; nombre_mostrado: string; nombre?: string };

@Component({
  selector: 'app-registro',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './registro.html',
  styleUrl: './registro.scss',
})
export default class RegistroComponent {
  private destroyRef = inject(DestroyRef);
  private route = inject(ActivatedRoute);

  // ====== route ======
  codigo = signal<string>('');

  // ✅ reunión (para mostrar nombre)
  reunion = signal<any | null>(null);
  reunionNombre = computed(() => this.reunion()?.nombre_evento ?? '');

  // ✅ true solo si la reunión es de tipo DESPLIEGUE
  esReunionDespliegue = computed(() => {
    return (this.reunion()?.tipo_documento ?? '').toUpperCase() === 'DESPLIEGUE';
  });

  // ✅ vista: form o success
  vista = signal<'form' | 'success'>('form');

  // ====== UI ======
  loading = signal(false);
  errorMsg = signal<string | null>(null);
  okMsg = signal<string | null>(null);

  // ====== catálogos (BD) ======
  procesos = signal<CatalogoLite[]>([]);
  subprocesos = signal<CatalogoLite[]>([]);
  lineasTrabajo = signal<CatalogoLite[]>([]);

  // ✅ signal reactivo del proceso seleccionado (para que el *ngIf funcione)
  procesoIdSeleccionado = signal<number | null>(null);

  // ✅ computed: obtiene el proceso seleccionado desde el catálogo
  private procesoSeleccionado = computed(() => {
    const id = this.procesoIdSeleccionado();
    if (!id) return null;
    return this.procesos().find((p) => p.id === id) ?? null;
  });

  // ✅ computed robusto: identifica EXTERNO por codigo o por texto mostrado
  esProcesoExterno = computed(() => {
    const p = this.procesoSeleccionado();
    if (!p) return false;

    const codigo = (p.codigo ?? '').trim().toUpperCase();
    const texto = (p.nombre_mostrado ?? p.nombre ?? p.codigo ?? '').trim().toUpperCase();

    // acepta ambos casos: codigo exacto EXTERNO o texto "EXTERNO"
    return codigo === 'EXTERNO' || texto === 'EXTERNO';
  });

  // ====== form ======
  form!: FormGroup;

  // Regex
  private readonly nombreRegex = /^[A-Za-zÁÉÍÓÚáéíóúÑñÜü\s]+$/;
  private readonly soloNumerosRegex = /^\d+$/;

  constructor(
    private fb: FormBuilder,
    private catalogos: CatalogosService,
    private reuniones: ReunionesService
  ) {
    this.form = this.fb.group({
      nombre_completo: [
        '',
        [
          Validators.required,
          Validators.minLength(3),
          Validators.maxLength(200),
          Validators.pattern(this.nombreRegex),
        ],
      ],
      identificacion: [
        '',
        [
          Validators.required,
          Validators.minLength(6),
          Validators.maxLength(30),
          Validators.pattern(this.soloNumerosRegex),
        ],
      ],

      // ✅ correo NO obligatorio
      correo: ['', [Validators.maxLength(200), Validators.email]],

      cargo: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(150)]],
      modalidad_asistencia: ['PRESENCIAL', Validators.required],

      // ✅ solo Proceso obligatorio
      proceso_id: ['', Validators.required],
      subproceso_id: [{ value: '', disabled: true }],
      linea_trabajo_id: [{ value: '', disabled: true }],

      // ✅ Solo si Proceso = EXTERNO
      institucion_externa: [''],
    });
  }

  ngOnInit() {
    // 1) codigo desde ruta
    this.route.paramMap.pipe(takeUntilDestroyed(this.destroyRef)).subscribe((pm) => {
      const c = (pm.get('codigo') ?? '').trim();
      this.codigo.set(c);
      if (c) this.cargarReunion();
    });

    // 2) procesos desde BD
    this.catalogos
      .procesos()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (x: CatalogoItem[]) => {
          const mapped = (x ?? []).map((p: any) => ({
            id: Number(p.id),
            codigo: String(p.codigo),
            nombre_mostrado: String(p.nombre_mostrado ?? p.nombre ?? p.codigo),
            nombre: p.nombre ? String(p.nombre) : undefined,
          }));

          this.procesos.set(mapped);

          // ✅ IMPORTANTE: al llegar el catálogo, sincroniza el signal del proceso seleccionado
          const raw = this.form.get('proceso_id')?.value;
          const current = raw ? Number(raw) : null;
          this.procesoIdSeleccionado.set(current);

          // ✅ y recalcula validadores de institución por si ya estaba seleccionado EXTERNO
          this.aplicarReglaInstitucionExterna();
        },
        error: () => this.procesos.set([]),
      });

    // 3) Proceso -> subprocesos + regla EXTERNO
    this.form.controls['proceso_id'].valueChanges
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((idProceso) => {
        const idNum = idProceso ? Number(idProceso) : null;
        this.procesoIdSeleccionado.set(idNum);

        // ✅ regla institución externa
        this.aplicarReglaInstitucionExterna();

        // ===== Cascada subproceso/linea =====
        this.subprocesos.set([]);
        this.lineasTrabajo.set([]);

        this.form.controls['subproceso_id'].reset('');
        this.form.controls['linea_trabajo_id'].reset('');

        this.form.controls['subproceso_id'].disable({ emitEvent: false });
        this.form.controls['linea_trabajo_id'].disable({ emitEvent: false });

        if (!idNum) return;

        this.catalogos
          .subprocesos(idNum)
          .pipe(takeUntilDestroyed(this.destroyRef))
          .subscribe({
            next: (subs) => {
              const mapped = (subs ?? []).map((s: any) => ({
                id: Number(s.id),
                codigo: String(s.codigo),
                nombre_mostrado: String(s.nombre_mostrado ?? s.nombre ?? s.codigo),
                nombre: s.nombre ? String(s.nombre) : undefined,
              }));
              this.subprocesos.set(mapped);
              if (mapped.length > 0) this.form.controls['subproceso_id'].enable({ emitEvent: false });
            },
            error: () => this.subprocesos.set([]),
          });

        // 🟡 Logs temporales (quita luego)
        // console.log('idProceso:', idNum);
        // console.log('seleccionado:', this.procesoSeleccionado());
        // console.log('esExterno:', this.esProcesoExterno());
      });

    // 4) Subproceso -> lineas
    this.form.controls['subproceso_id'].valueChanges
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((idSub) => {
        this.lineasTrabajo.set([]);
        this.form.controls['linea_trabajo_id'].reset('');
        this.form.controls['linea_trabajo_id'].disable({ emitEvent: false });

        if (!idSub) return;

        const id = Number(idSub);
        this.catalogos
          .lineasTrabajo(id)
          .pipe(takeUntilDestroyed(this.destroyRef))
          .subscribe({
            next: (lins) => {
              const mapped = (lins ?? []).map((l: any) => ({
                id: Number(l.id),
                codigo: String(l.codigo),
                nombre_mostrado: String(l.nombre_mostrado ?? l.nombre ?? l.codigo),
                nombre: l.nombre ? String(l.nombre) : undefined,
              }));
              this.lineasTrabajo.set(mapped);
              if (mapped.length > 0) this.form.controls['linea_trabajo_id'].enable({ emitEvent: false });
            },
            error: () => this.lineasTrabajo.set([]),
          });
      });
  }

  // ✅ aplica validadores + limpia campo si NO es externo
  private aplicarReglaInstitucionExterna() {
    const instCtrl = this.form.controls['institucion_externa'];

    if (this.esProcesoExterno()) {
      instCtrl.setValidators([
        Validators.required,
        Validators.minLength(3),
        Validators.maxLength(200),
      ]);
    } else {
      instCtrl.clearValidators();
      instCtrl.setValue('', { emitEvent: false });
    }

    instCtrl.updateValueAndValidity({ emitEvent: false });
  }

  cargarReunion() {
    const codigo = this.codigo();
    if (!codigo) return;

    this.reuniones
      .obtenerReunion(codigo)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (res: any) => this.reunion.set(res ?? null),
        error: () => this.reunion.set(null),
      });
  }

  submit() {
    this.okMsg.set(null);
    this.errorMsg.set(null);

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const codigo = this.codigo();
    if (!codigo) {
      this.errorMsg.set('Código de reunión inválido.');
      return;
    }

    const raw = this.form.getRawValue();

    const correoFinal =
      raw.correo && String(raw.correo).trim().length > 0 ? String(raw.correo).trim() : null;

    const institucionFinal =
      raw.institucion_externa && String(raw.institucion_externa).trim().length > 0
        ? String(raw.institucion_externa).trim()
        : null;

    const payload: any = {
      nombre_completo: (raw.nombre_completo ?? '').trim(),
      identificacion: (raw.identificacion ?? '').trim(),
      correo: correoFinal,
      cargo: (raw.cargo ?? '').trim(),
      modalidad_asistencia: String(raw.modalidad_asistencia ?? 'PRESENCIAL').toUpperCase(),

      proceso_id: raw.proceso_id ? Number(raw.proceso_id) : null,
      subproceso_id: raw.subproceso_id ? Number(raw.subproceso_id) : null,
      linea_trabajo_id: raw.linea_trabajo_id ? Number(raw.linea_trabajo_id) : null,

      // ✅ solo tiene valor si aplica (y si el user lo diligenció)
      institucion_externa: institucionFinal,
    };

    this.loading.set(true);

    this.reuniones
      .registrarAsistente(codigo, payload)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (res: any) => {
          this.loading.set(false);
          const envio = res?.email_enviado ? ' Se envió confirmación al correo.' : '';
          this.okMsg.set('Asistencia registrada correctamente.' + envio);
          this.vista.set('success');
        },
        error: (err) => {
          this.loading.set(false);
          this.errorMsg.set(this.extractFastApiError(err));
        },
      });
  }

  volverAFormulario() {
    this.errorMsg.set(null);
    this.okMsg.set(null);
    this.vista.set('form');

    this.form.reset({
      modalidad_asistencia: 'PRESENCIAL',
      proceso_id: '',
      subproceso_id: '',
      linea_trabajo_id: '',
      correo: '',
      institucion_externa: '',
    });

    this.procesoIdSeleccionado.set(null);
    this.subprocesos.set([]);
    this.lineasTrabajo.set([]);

    this.form.controls['subproceso_id'].disable({ emitEvent: false });
    this.form.controls['linea_trabajo_id'].disable({ emitEvent: false });

    // ✅ deja el campo sin requerimiento
    this.aplicarReglaInstitucionExterna();
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
    return 'Error registrando el asistente.';
  }

  // ✅ EXACTO como en crear.ts
  soloLetras(event: KeyboardEvent) {
    const key = event.key;
    if (
      key === 'Backspace' ||
      key === 'Tab' ||
      key === 'Enter' ||
      key === 'ArrowLeft' ||
      key === 'ArrowRight' ||
      key === 'Delete'
    )
      return;

    const ok = /^[A-Za-zÁÉÍÓÚáéíóúÑñÜü\s]$/.test(key);
    if (!ok) event.preventDefault();
  }

  // ✅ EXACTO como en crear.ts
  soloNumeros(event: KeyboardEvent) {
    const key = event.key;
    if (
      key === 'Backspace' ||
      key === 'Tab' ||
      key === 'Enter' ||
      key === 'ArrowLeft' ||
      key === 'ArrowRight' ||
      key === 'Delete'
    )
      return;

    const ok = /^\d$/.test(key);
    if (!ok) event.preventDefault();
  }
}
