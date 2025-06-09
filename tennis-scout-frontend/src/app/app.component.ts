import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { ApiService } from './services/api.service';
import { ProcessingStepsComponent } from './shared/processing-steps/processing-steps.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    RouterOutlet,
    RouterLink,
    RouterLinkActive,
    MatIconModule,
    MatSnackBarModule,
    ProcessingStepsComponent
  ],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit {
  title = 'Tennis Scout AI';
  
  constructor(
    private apiService: ApiService,
    private snackBar: MatSnackBar
  ) {}
  
  ngOnInit(): void {
    this.snackBar.dismiss();
    
    setTimeout(() => {
      this.snackBar.dismiss();
      this.clearAllNotifications();
    }, 100);
    
    console.log('🎾 Tennis Scout AI initialized');
  }
  
  private clearAllNotifications(): void {
    try {
      const containers = document.querySelectorAll('snack-bar-container, .mat-snack-bar-container');
      containers.forEach(container => container.remove());
    } catch (error) {
      console.log('Cleanup attempted');
    }
  }
  
  private checkBackendConnection(): void {
    this.apiService.checkConnection().subscribe({
      next: (isConnected) => {
        if (isConnected) {
          console.log('✅ Backend connected successfully');
        } else {
          console.warn('⚠️ Backend connection issues');
        }
      },
      error: (error) => {
        console.error('❌ Backend connection failed:', error);
        this.snackBar.open('❌ Cannot connect to backend', 'Dismiss', {
          duration: 5000,
          panelClass: ['error-snackbar']
        });
      }
    });
  }
}