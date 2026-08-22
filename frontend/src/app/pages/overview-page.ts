import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ApiClient, SystemSummary } from '../api-client';

@Component({
  selector: 'app-overview-page',
  imports: [CommonModule, RouterLink],
  templateUrl: './overview-page.html',
  styleUrl: './overview-page.scss'
})
export class OverviewPage implements OnInit {
  summary?: SystemSummary;
  loading = true;
  error = '';

  constructor(
    private readonly api: ApiClient,
    private readonly changeDetector: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.api.systemSummary().subscribe({
      next: (summary) => {
        this.summary = summary;
        this.loading = false;
        this.changeDetector.detectChanges();
      },
      error: () => {
        this.error = 'The API is not reachable. Start FastAPI at http://localhost:8000.';
        this.loading = false;
        this.changeDetector.detectChanges();
      }
    });
  }
}
