import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { Router } from '@angular/router';
import { Subject, takeUntil } from 'rxjs';
import { FormsModule } from '@angular/forms';

import { MatchesService, ProcessedMatch } from '../../services/matches.service';

@Component({
  selector: 'app-matches',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatCardModule,
    MatIconModule,
    MatButtonModule,
    MatChipsModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
    MatFormFieldModule,
    MatInputModule
  ],
  templateUrl: './matches.component.html',
  styleUrls: ['./matches.component.scss']
})
export class MatchesComponent implements OnInit, OnDestroy {
  matches: ProcessedMatch[] = [];
  filteredMatches: ProcessedMatch[] = [];
  isLoading = false;
  searchTerm = '';
  selectedStatus: 'all' | 'completed' | 'processing' | 'failed' = 'all';
  
  private destroy$ = new Subject<void>();

  constructor(
    private matchesService: MatchesService,
    private snackBar: MatSnackBar,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loadMatches();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadMatches(): void {
    this.isLoading = true;
    
    this.matchesService.getAllMatches()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (matches) => {
          this.matches = matches;
          this.applyFilters();
          this.isLoading = false;
        },
        error: (error) => {
          console.error('Failed to load matches:', error);
          this.snackBar.open('❌ Failed to load matches', 'Close', {
            duration: 5000,
            panelClass: ['error-snackbar']
          });
          this.isLoading = false;
        }
      });
  }

  onSearch(): void {
    this.applyFilters();
  }

  onStatusFilter(status: 'all' | 'completed' | 'processing' | 'failed'): void {
    this.selectedStatus = status;
    this.applyFilters();
  }

  private applyFilters(): void {
    let filtered = [...this.matches];

    if (this.selectedStatus !== 'all') {
      filtered = filtered.filter(match => match.status === this.selectedStatus);
    }

    if (this.searchTerm.trim()) {
      const term = this.searchTerm.toLowerCase();
      filtered = filtered.filter(match => 
        match.title.toLowerCase().includes(term) ||
        match.video_id.toLowerCase().includes(term) ||
        match.players_detected?.some(player => player.toLowerCase().includes(term))
      );
    }

    this.filteredMatches = filtered;
  }

  analyzeMatch(match: ProcessedMatch): void {
    if (match.status === 'completed') {
      this.router.navigate(['/analysis'], { 
        queryParams: { matchId: match.id, videoId: match.video_id }
      });
    } else {
      this.snackBar.open('⚠️ Match must be completed before analysis', 'Close', {
        duration: 3000,
        panelClass: ['warning-snackbar']
      });
    }
  }

  deleteMatch(match: ProcessedMatch): void {
    if (confirm(`Are you sure you want to delete "${match.title}"?`)) {
      this.matchesService.deleteMatch(match.id)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: () => {
            this.matches = this.matches.filter(m => m.id !== match.id);
            this.applyFilters();
            this.snackBar.open('✅ Match deleted successfully', 'Close', {
              duration: 3000,
              panelClass: ['success-snackbar']
            });
          },
          error: (error) => {
            console.error('Failed to delete match:', error);
            this.snackBar.open('❌ Failed to delete match', 'Close', {
              duration: 5000,
              panelClass: ['error-snackbar']
            });
          }
        });
    }
  }

  reprocessMatch(match: ProcessedMatch): void {
    this.matchesService.reprocessMatch(match.id)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.snackBar.open('🔄 Match reprocessing started', 'Close', {
            duration: 3000,
            panelClass: ['success-snackbar']
          });
          this.loadMatches();
        },
        error: (error) => {
          console.error('Failed to reprocess match:', error);
          this.snackBar.open('❌ Failed to reprocess match', 'Close', {
            duration: 5000,
            panelClass: ['error-snackbar']
          });
        }
      });
  }

  viewOnYouTube(videoId: string): void {
    window.open(`https://www.youtube.com/watch?v=${videoId}`, '_blank');
  }

  getStatusColor(status: string): string {
    switch (status) {
      case 'completed': return '#4ade80';
      case 'processing': return '#f59e0b';
      case 'failed': return '#ef4444';
      default: return '#6b7280';
    }
  }

  getStatusIcon(status: string): string {
    switch (status) {
      case 'completed': return 'check_circle';
      case 'processing': return 'hourglass_empty';
      case 'failed': return 'error';
      default: return 'help';
    }
  }

  formatDuration(seconds?: number): string {
    if (!seconds) return 'Unknown';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  }

  formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  }

  getThumbnailUrl(videoId: string): string {
    return `https://img.youtube.com/vi/${videoId}/mqdefault.jpg`;
  }

  getMatchesCount(): { total: number; completed: number; processing: number; failed: number } {
    return {
      total: this.matches.length,
      completed: this.matches.filter(m => m.status === 'completed').length,
      processing: this.matches.filter(m => m.status === 'processing').length,
      failed: this.matches.filter(m => m.status === 'failed').length
    };
  }

  goToUpload(): void {
    this.router.navigate(['/upload']);
  }

  clearFilters(): void {
    this.searchTerm = '';
    this.selectedStatus = 'all';
    this.applyFilters();
  }
  
}