import { Routes } from '@angular/router';

import CrearComponent from './features/reuniones/crear/crear';
import ConsultaComponent from './features/reuniones/consulta/consulta';
import ConfirmacionComponent from './features/reuniones/confirmacion/confirmacion';
import RegistroComponent from './features/reuniones/registro/registro';

export const routes: Routes = [
  { path: '', redirectTo: 'reuniones/crear', pathMatch: 'full' },
  { path: 'reuniones/crear', component: CrearComponent },
  { path: 'reuniones/consulta', component: ConsultaComponent },
  { path: 'reuniones/confirmacion/:codigo', component: ConfirmacionComponent },
  { path: 'registro/:codigo', component: RegistroComponent },
  { path: '**', redirectTo: 'reuniones/crear' },
];
