import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiClient, FeederChangesResponse, FeederHistoryResponse } from '../api-client';

@Component({
  selector: 'app-history-page',
  imports: [CommonModule, FormsModule],
  templateUrl: './history-page.html',
  styleUrl: './history-page.scss'
})
export class HistoryPage {
  feederId = 'DEMO-F1';
  history?: FeederHistoryResponse;
  changes?: FeederChangesResponse;
  loading = false;
  error = '';

  constructor(
    private readonly api: ApiClient,
    private readonly changeDetector: ChangeDetectorRef
  ) {}

  load(): void {
    const id = this.feederId.trim();
    if (!id) return;
    this.loading = true;
    this.error = '';
    this.history = undefined;
    this.changes = undefined;
    this.changeDetector.detectChanges();

    this.api.feederHistory(id).subscribe({
      next: (history) => {
        this.history = history;
        this.changeDetector.detectChanges();
        this.api.feederChanges(id).subscribe({
          next: (changes) => {
            this.changes = changes;
            this.loading = false;
            this.changeDetector.detectChanges();
          },
          error: () => {
            this.loading = false;
            this.changeDetector.detectChanges();
          }
        });
      },
      error: (error) => {
        this.error = error?.error?.error?.message ?? 'History lookup failed.';
        this.loading = false;
        this.changeDetector.detectChanges();
      }
    });
  }
}
