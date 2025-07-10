import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { Observable } from 'rxjs';

import { UploadService } from '../../services/upload.service';
import { ProcessingStep } from '../../models/processing-step.interface';

@Component({
  selector: 'app-processing-steps',
  standalone: true,
  imports: [
    CommonModule, 
    MatIconModule, 
    MatProgressBarModule, 
    MatProgressSpinnerModule
  ],
  templateUrl: './processing-steps.component.html',
  styleUrls: ['./processing-steps.component.scss']
})
export class ProcessingStepsComponent implements OnInit {
  isProcessing$: Observable<boolean>;
  currentStep$: Observable<ProcessingStep | null>;

  constructor(private uploadService: UploadService) {
    this.isProcessing$ = this.uploadService.isProcessing$;
    this.currentStep$ = this.uploadService.processingSteps$;
  }

  ngOnInit(): void {}

  getStepIcon(step: number, status: string): string {
    if (status === 'completed') return 'check_circle';
    if (status === 'processing') return 'hourglass_empty';
    if (status === 'error') return 'error';
    return 'radio_button_unchecked';
  }

  getStepClass(step: number, currentStep: ProcessingStep | null): string {
    if (!currentStep) return 'pending';
    
    if (step < currentStep.step) return 'completed';
    if (step === currentStep.step) return currentStep.status;
    return 'pending';
  }
}