// src/app/app.routes.ts
import { Routes } from '@angular/router';
import { UploadComponent } from './components/upload/upload.component';
import { AnalysisComponent } from './components/analysis/analysis.component';
import { MatchesComponent } from './components/matches/matches.component';

export const routes: Routes = [
  { path: '', redirectTo: '/upload', pathMatch: 'full' },
  { path: 'upload', component: UploadComponent },
  { path: 'analysis', component: AnalysisComponent },
  { path: 'matches', component: MatchesComponent },
  { path: '**', redirectTo: '/upload' }
];