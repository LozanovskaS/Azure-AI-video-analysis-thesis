import { Injectable } from '@angular/core';
import { Observable, BehaviorSubject } from 'rxjs';
import { ApiService } from './api.service';
import { UploadRequest, UploadResponse } from '../models/upload.interface';
import { ProcessingStep } from '../models/processing-step.interface';

@Injectable({
  providedIn: 'root'
})
export class UploadService {
  private processingSteps = new BehaviorSubject<ProcessingStep | null>(null);
  private isProcessing = new BehaviorSubject<boolean>(false);

  constructor(private apiService: ApiService) {}

  get processingSteps$(): Observable<ProcessingStep | null> {
    return this.processingSteps.asObservable();
  }

  get isProcessing$(): Observable<boolean> {
    return this.isProcessing.asObservable();
  }

  extractTranscript(request: UploadRequest): Observable<any> {
    this.updateProcessingStep(1, 4, 'Extracting transcript...', 'processing');
    return this.apiService.post('transcript/extract', request);
  }

  cleanTranscript(videoId: string): Observable<any> {
    this.updateProcessingStep(2, 4, 'Cleaning transcript with AI...', 'processing');
    return this.apiService.post(`transcript/clean/${videoId}`, {});
  }

  indexTranscript(videoId: string): Observable<any> {
    this.updateProcessingStep(3, 4, 'Indexing for search...', 'processing');
    return this.apiService.post(`search/index/${videoId}`, {});
  }

  processVideo(input: string): Observable<UploadResponse> {
    this.isProcessing.next(true);
    this.resetProcessing();
    
    return new Observable(observer => {
      this.extractTranscript({ input }).subscribe({
        next: (extractResult) => {
          console.log('Extract result:', extractResult);
          
          if (!extractResult.success || !extractResult.video_id) {
            this.updateProcessingStep(1, 4, 'Failed to extract transcript', 'error');
            this.isProcessing.next(false);
            observer.error({ message: extractResult.message || 'Failed to extract transcript' });
            return;
          }

          const videoId = extractResult.video_id;
          const videoTitle = extractResult.title || 'Unknown Title';
          
          this.updateProcessingStep(1, 4, 'Transcript extracted successfully', 'completed');

          setTimeout(() => {
            this.cleanTranscript(videoId).subscribe({
              next: (cleanResult) => {
                console.log('Clean result:', cleanResult);
                this.updateProcessingStep(2, 4, 'Transcript cleaned successfully', 'completed');

                setTimeout(() => {
                  this.indexTranscript(videoId).subscribe({
                    next: (indexResult) => {
                      console.log('Index result:', indexResult);
                      this.updateProcessingStep(3, 4, 'Transcript indexed successfully', 'completed');

                      setTimeout(() => {
                        this.updateProcessingStep(4, 4, 'Processing complete!', 'completed');
                        this.isProcessing.next(false);
                        
                        observer.next({
                          success: true,
                          message: `Successfully processed: ${videoTitle}`,
                          video_id: videoId,
                          title: videoTitle
                        });
                        observer.complete();
                      }, 1000);
                    },
                    error: (indexError) => {
                      console.warn('Indexing failed, but continuing:', indexError);
                      this.updateProcessingStep(3, 4, 'Indexing had issues (continuing)', 'completed');
                      
                      setTimeout(() => {
                        this.updateProcessingStep(4, 4, 'Processing complete with warnings', 'completed');
                        this.isProcessing.next(false);
                        
                        observer.next({
                          success: true,
                          message: `Processed with warnings: ${videoTitle}`,
                          video_id: videoId,
                          title: videoTitle
                        });
                        observer.complete();
                      }, 1000);
                    }
                  });
                }, 2000);
              },
              error: (cleanError) => {
                console.warn('Cleaning failed, but continuing:', cleanError);
                this.updateProcessingStep(2, 4, 'Cleaning had issues (continuing)', 'completed');
                
                setTimeout(() => {
                  this.indexTranscript(videoId).subscribe({
                    next: (indexResult) => {
                      this.updateProcessingStep(3, 4, 'Transcript indexed successfully', 'completed');
                      
                      setTimeout(() => {
                        this.updateProcessingStep(4, 4, 'Processing complete with warnings', 'completed');
                        this.isProcessing.next(false);
                        
                        observer.next({
                          success: true,
                          message: `Processed with warnings: ${videoTitle}`,
                          video_id: videoId,
                          title: videoTitle
                        });
                        observer.complete();
                      }, 1000);
                    },
                    error: (indexError) => {
                      this.updateProcessingStep(4, 4, 'Processing complete with warnings', 'completed');
                      this.isProcessing.next(false);
                      
                      observer.next({
                        success: true,
                        message: `Basic processing complete: ${videoTitle}`,
                        video_id: videoId,
                        title: videoTitle
                      });
                      observer.complete();
                    }
                  });
                }, 2000);
              }
            });
          }, 3000);
        },
        error: (extractError) => {
          console.error('Extract error:', extractError);
          this.updateProcessingStep(1, 4, 'Failed to extract transcript', 'error');
          this.isProcessing.next(false);
          observer.error(extractError);
        }
      });
    });
  }

  testExtraction(input: string): Observable<any> {
    return this.apiService.post('transcript/extract', { input });
  }

  resetProcessing(): void {
    this.processingSteps.next(null);
  }

  private updateProcessingStep(step: number, total: number, message: string, status: ProcessingStep['status']): void {
    this.processingSteps.next({ step, total, message, status });
  }
}