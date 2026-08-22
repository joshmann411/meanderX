import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiClient, FeederResponse, SubstationResponse } from '../api-client';
import { GeometryPreview } from '../geometry-preview/geometry-preview';

@Component({
  selector: 'app-substations-page',
  imports: [CommonModule, FormsModule, GeometryPreview],
  templateUrl: './substations-page.html',
  styleUrl: './substations-page.scss'
})
export class SubstationsPage {
  substationId = 'DEMO-SUB-A';
  substation?: SubstationResponse;
  feeders: FeederResponse[] = [];
  loading = false;
  error = '';

  constructor(
    private readonly api: ApiClient,
    private readonly changeDetector: ChangeDetectorRef
  ) {}

  load(): void {
    const id = this.substationId.trim();
    if (!id) return;
    this.loading = true;
    this.error = '';
    this.substation = undefined;
    this.feeders = [];
    this.changeDetector.detectChanges();

    this.api.substation(id).subscribe({
      next: (substation) => {
        this.substation = substation;
        this.changeDetector.detectChanges();
        this.api.substationFeeders(id).subscribe({
          next: (response) => {
            this.feeders = response.items;
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
        this.error = error?.error?.error?.message ?? 'Substation lookup failed.';
        this.loading = false;
        this.changeDetector.detectChanges();
      }
    });
  }
}
