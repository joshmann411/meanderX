import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiClient, FeederResponse, QueueResponse } from '../api-client';
import { GeometryPreview } from '../geometry-preview/geometry-preview';

@Component({
  selector: 'app-feeders-page',
  imports: [CommonModule, FormsModule, GeometryPreview],
  templateUrl: './feeders-page.html',
  styleUrl: './feeders-page.scss'
})
export class FeedersPage {
  feederId = 'DEMO-F1';
  substationId = '';
  minPvThermal?: number;
  results: FeederResponse[] = [];
  selected?: FeederResponse;
  queue?: QueueResponse;
  loading = false;
  error = '';

  constructor(
    private readonly api: ApiClient,
    private readonly changeDetector: ChangeDetectorRef
  ) {}

  search(): void {
    this.loading = true;
    this.error = '';
    this.changeDetector.detectChanges();
    this.api.searchFeeders({
      feederId: this.feederId.trim() || undefined,
      substationId: this.substationId.trim() || undefined,
      minPvThermal: this.minPvThermal,
      limit: 30
    }).subscribe({
      next: (response) => {
        this.results = response.items;
        this.loading = false;
        if (response.items.length) this.select(response.items[0]);
        this.changeDetector.detectChanges();
      },
      error: (error) => {
        this.error = error?.error?.error?.message ?? 'Feeder search failed.';
        this.loading = false;
        this.changeDetector.detectChanges();
      }
    });
  }

  select(feeder: FeederResponse): void {
    this.selected = feeder;
    this.queue = undefined;
    this.changeDetector.detectChanges();
    this.api.queue(feeder.feederId).subscribe({
      next: (queue) => {
        this.queue = queue;
        this.changeDetector.detectChanges();
      },
      error: () => {
        this.queue = undefined;
        this.changeDetector.detectChanges();
      }
    });
  }
}
