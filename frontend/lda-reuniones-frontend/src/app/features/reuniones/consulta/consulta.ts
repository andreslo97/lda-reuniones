import { CommonModule } from '@angular/common';
import { Component, signal } from '@angular/core';
import { ReactiveFormsModule, FormBuilder, Validators, FormGroup } from '@angular/forms';
import { ReunionesService } from '../../../core/api/reuniones.service';

@Component({
  selector: 'app-consulta',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './consulta.html',
  styleUrl: './consulta.scss',
})
export default class ConsultaComponent {
  loading = signal(false);
  loadingAsistentes = signal(false);

  errorMsg = signal<string | null>(null);
  data = signal<any | null>(null);

  // asistentes asociados a la reunión
  asistentes = signal<any[]>([]);

  // formulario
  form!: FormGroup;

  constructor(
    private fb: FormBuilder,
    private reuniones: ReunionesService
  ) {
    this.form = this.fb.group({
      codigo: ['', [Validators.required, Validators.minLength(6), Validators.maxLength(50)]],
    });
  }

  consultar() {
    this.errorMsg.set(null);
    this.data.set(null);
    this.asistentes.set([]);

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const codigo = (this.form.value.codigo ?? '').trim();
    if (!codigo) return;

    this.loading.set(true);

    this.reuniones.detalle(codigo).subscribe({
      next: (res) => {
        this.loading.set(false);
        this.data.set(res);

        // ✅ solo si la reunión existe, cargamos asistentes
        this.cargarAsistentes(codigo);
      },
      error: (err) => {
        this.loading.set(false);
        this.errorMsg.set(
          err?.error?.detail ?? 'No se encontró la reunión con ese código.'
        );
      },
    });
  }

  // =========================
  // Asistentes
  // =========================
  cargarAsistentes(codigo: string) {
    this.loadingAsistentes.set(true);

    this.reuniones.listarAsistentes(codigo).subscribe({
      next: (res: any) => {
        this.asistentes.set(res?.asistentes ?? []);
        this.loadingAsistentes.set(false);
      },
      error: () => {
        this.asistentes.set([]);
        this.loadingAsistentes.set(false);
      },
    });
  }

  // =========================
  // QR
  // =========================
  descargarQr() {
    const codigo = (this.form.value.codigo ?? '').trim();
    if (!codigo) return;

    window.open(this.reuniones.qrUrl(codigo), '_blank');
  }
}
