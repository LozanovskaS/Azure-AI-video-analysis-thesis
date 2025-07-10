import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Observable, Subject, takeUntil, distinctUntilChanged, debounceTime } from 'rxjs';

import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-connection-status',
  standalone: true,
  imports: [CommonModule, MatIconModule, MatButtonModule, MatTooltipModule],
  template: `

    <div *ngIf="(isConnected$ | async) === false" 
         class="connection-status disconnected"
         matTooltip="Backend connection lost">
      <mat-icon>wifi_off</mat-icon>
      <span>Disconnected</span>
      <button mat-icon-button 
              (click)="retryConnection()" 
              matTooltip="Retry connection">
        <mat-icon>refresh</mat-icon>
      </button>
    </div>
    
    <div *ngIf="showReconnected" 
         class="connection-status connected">
      <mat-icon>wifi</mat-icon>
      <span>Connected</span>
    </div>
  `,
  styles: [`
    .connection-status {
      position: fixed;
      top: 20px;
      right: 20px;
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: 20px;
      backdrop-filter: blur(10px);
      z-index: 1000;
      font-size: 13px;
      font-weight: 500;
      animation: slideIn 0.3s ease-out;
      
      &.disconnected {
        background: rgba(239, 68, 68, 0.9);
        color: white;
        border: 1px solid rgba(239, 68, 68, 0.3);
      }
      
      &.connected {
        background: rgba(34, 197, 94, 0.9);
        color: white;
        border: 1px solid rgba(34, 197, 94, 0.3);
        animation: slideIn 0.3s ease-out, slideOut 0.3s ease-out 1.7s forwards;
      }
      
      button {
        color: white;
        width: 24px;
        height: 24px;
        
        mat-icon {
          font-size: 16px;
          width: 16px;
          height: 16px;
        }
      }
    }
    
    @keyframes slideIn {
      from {
        opacity: 0;
        transform: translateX(100%);
      }
      to {
        opacity: 1;
        transform: translateX(0);
      }
    }
    
    @keyframes slideOut {
      from {
        opacity: 1;
        transform: translateX(0);
      }
      to {
        opacity: 0;
        transform: translateX(100%);
      }
    }
  `]
})
export class ConnectionStatusComponent implements OnInit, OnDestroy {
  isConnected$: Observable<boolean>;
  showReconnected = false;
  private destroy$ = new Subject<void>();
  private previousConnectionState: boolean | null = null;

  constructor(private apiService: ApiService) {
    this.isConnected$ = this.apiService.isConnected$;
  }

  ngOnInit(): void {
    this.isConnected$
      .pipe(
        takeUntil(this.destroy$),
        distinctUntilChanged(),
        debounceTime(500)
      )
      .subscribe(isConnected => {
        if (isConnected && this.previousConnectionState === false) {
          this.showReconnected = true;
          
          setTimeout(() => {
            this.showReconnected = false;
          }, 2000);
        }
        
        this.previousConnectionState = isConnected;
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  retryConnection(): void {
    this.apiService.checkConnection().subscribe();
  }
}