import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { Router } from '@angular/router';
import { Subject, takeUntil } from 'rxjs';

import { UploadService } from '../../services/upload.service';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-upload',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatCardModule,
    MatIconModule,
    MatButtonModule,
    MatInputModule,
    MatFormFieldModule,
    MatProgressSpinnerModule,
    MatSnackBarModule
  ],
  templateUrl: './upload.component.html',
  styleUrls: ['./upload.component.scss']
})
export class UploadComponent implements OnInit, OnDestroy {
  uploadForm: FormGroup;
  isProcessing = false;
  successMessage = '';
  errorMessage = '';
  private destroy$ = new Subject<void>();

  constructor(
    private fb: FormBuilder,
    private uploadService: UploadService,
    private apiService: ApiService,
    private snackBar: MatSnackBar,
    private router: Router
  ) {
    this.uploadForm = this.fb.group({
      input: ['', [Validators.required]]
    });
  }

  ngOnInit(): void {
    this.snackBar.dismiss();
    
    setTimeout(() => {
      this.snackBar.dismiss();
    }, 100);
    
    this.uploadService.isProcessing$
      .pipe(takeUntil(this.destroy$))
      .subscribe(processing => {
        this.isProcessing = processing;
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  onSubmit(): void {
    if (this.uploadForm.valid && !this.isProcessing) {
      const input = this.uploadForm.get('input')?.value.trim();
      
      this.clearMessages();
      
      this.uploadService.processVideo(input)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: (result) => {
            this.successMessage = `✅ Successfully processed: ${result.title}`;
            this.uploadForm.reset();
            
            const snackBarRef = this.snackBar.open('🎾 Video ready for analysis!', 'Start Analysis', {
              duration: 5000,
              panelClass: ['success-snackbar']
            });

            setTimeout(() => {
              this.router.navigate(['/analysis']);
            }, 1500);

            snackBarRef.onAction().subscribe(() => {
              this.router.navigate(['/analysis']);
            });
          },
          error: (error) => {
            this.errorMessage = error.message || 'Failed to process video';
            this.snackBar.open('❌ Processing failed', 'Close', {
              duration: 5000,
              panelClass: ['error-snackbar']
            });
          }
        });
    }
  }

  setTestVideo(videoId: string): void {
    this.uploadForm.patchValue({ input: videoId });
    this.clearMessages();
    this.snackBar.open(`✅ Set test video: ${videoId}`, 'Close', {
      duration: 2000
    });
  }

  testConnection(): void {
    console.log('🔧 Testing backend connection...');
    
    this.snackBar.dismiss();
    
    this.apiService.checkConnection()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (isConnected) => {
          if (isConnected) {
            console.log('✅ Backend connection successful');
            
            this.successMessage = 'Backend connected successfully!';
            
            setTimeout(() => {
              this.successMessage = '';
            }, 2000);
          } else {
            this.snackBar.open('⚠️ Connection issues', 'Close', {
              duration: 3000,
              panelClass: ['warning-snackbar']
            });
          }
        },
        error: (error) => {
          console.error('❌ Connection test failed:', error);
          this.snackBar.open('❌ Cannot connect to backend', 'Close', {
            duration: 5000,
            panelClass: ['error-snackbar']
          });
        }
      });
  }

  clearError(): void {
    this.errorMessage = '';
    this.snackBar.dismiss();
  }

  private clearMessages(): void {
    this.successMessage = '';
    this.errorMessage = '';
    this.snackBar.dismiss();
  }

  clearAllNotifications(): void {
    this.snackBar.dismiss();
    console.log('🧹 Cleared all notifications');
  }
}