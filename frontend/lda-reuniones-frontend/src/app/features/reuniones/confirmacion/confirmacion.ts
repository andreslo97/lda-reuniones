import { CommonModule } from '@angular/common';
import { Component, computed, signal } from '@angular/core';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { ReunionesService } from '../../../core/api/reuniones.service';
import { ReunionDetalle } from '../../../core/models/reuniones.model';

@Component({
  selector: 'app-confirmacion',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './confirmacion.html',
  styleUrl: './confirmacion.scss',
})
export default class ConfirmacionComponent {
  loading = signal(true);
  errorMsg = signal<string | null>(null);

  codigo = signal<string>('');
  detalle = signal<ReunionDetalle | null>(null);

  qrSrc = computed(() => {
    const c = this.codigo();
    return c ? this.reuniones.qrUrl(c) : '';
  });

  constructor(private route: ActivatedRoute, private reuniones: ReunionesService) {}

  ngOnInit() {
    const codigo = this.route.snapshot.paramMap.get('codigo') ?? '';
    this.codigo.set(codigo);

    if (!codigo) {
      this.loading.set(false);
      this.errorMsg.set('Código de reunión inválido.');
      return;
    }

    this.reuniones.detalle(codigo).subscribe({
      next: (x) => {
        this.detalle.set(x);
        this.loading.set(false);
      },
      error: (err) => {
        this.loading.set(false);
        this.errorMsg.set(err?.error?.detail ?? 'No se pudo cargar la reunión.');
      },
    });
  }

  copiarLink() {
    const link = this.detalle()?.link_registro ?? '';
    if (!link) return;
    navigator.clipboard.writeText(link);
  }

  descargarQR() {
    const url = this.qrSrc();
    if (!url) return;

    // descarga simple abriendo el recurso (sirve bien para png)
    const a = document.createElement('a');
    a.href = url;
    a.download = `QR_${this.codigo()}.png`;
    document.body.appendChild(a);
    a.click();
    a.remove();
  }
}
