import { Routes } from '@angular/router';
import { ArchitecturePage } from './pages/architecture-page';
import { FeedersPage } from './pages/feeders-page';
import { HistoryPage } from './pages/history-page';
import { OverviewPage } from './pages/overview-page';
import { SubstationsPage } from './pages/substations-page';

export const routes: Routes = [
  { path: '', component: OverviewPage, title: 'Overview' },
  { path: 'feeders', component: FeedersPage, title: 'Feeders' },
  { path: 'substations', component: SubstationsPage, title: 'Substations' },
  { path: 'history', component: HistoryPage, title: 'History' },
  { path: 'architecture', component: ArchitecturePage, title: 'Architecture' },
  { path: '**', redirectTo: '' }
];
