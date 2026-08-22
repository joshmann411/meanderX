import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

const API_BASE = 'http://localhost:8000/api/v1';

export interface SystemSummary {
  mode: string;
  environment: string;
  counts: {
    feeders: number;
    activeFeeders: number;
    substations: number;
    feederSnapshots: number;
    substationSnapshots: number;
    osmSubstations: number;
    acceptedOsmMatches: number;
  };
  latestIngestions: IngestionRun[];
  sources: {
    conedison: SourceCapability;
    osm: SourceCapability;
    queue: SourceCapability;
  };
  pipelineStages: string[];
}

export interface SourceCapability {
  available: boolean;
  note: string;
}

export interface IngestionRun {
  id: number;
  pipeline: string;
  source: string;
  status: string;
  extractedCount: number;
  validCount: number;
  loadedCount: number;
  rejectedCount: number;
  snapshotCreated: boolean;
  datasetHashPrefix?: string | null;
  completedAt?: string | null;
  metadata: Record<string, unknown>;
}

export interface FeederResponse {
  feederId: string;
  substationId?: string | null;
  hostingCapacity: {
    pvThermal?: number | string | null;
  };
  geometry?: GeoJsonGeometry | null;
  data: {
    source?: string | null;
    capturedAt?: string | null;
  };
}

export interface FeederSearchResponse {
  items: FeederResponse[];
  limit: number;
  offset: number;
}

export interface SubstationResponse {
  substationId: string;
  name?: string | null;
  geometry?: GeoJsonGeometry | null;
  geometrySource?: {
    source: string;
    osmId?: string | null;
    matchConfidence?: number | null;
    matchMethod?: string | null;
    distanceMeters?: number | null;
  } | null;
  connectedFeeders: {
    count: number;
  };
  sourceMetadata: Record<string, unknown>;
}

export interface QueueResponse {
  feederId: string;
  available: boolean;
  projectCount?: number | null;
  reason?: string | null;
}

export interface FeederHistoryResponse {
  feederId: string;
  history: Array<{
    capturedAt: string;
    pvThermal?: number | string | null;
    substationId?: string | null;
    geometry?: GeoJsonGeometry | null;
  }>;
}

export interface FeederChangesResponse {
  feederId: string;
  changes: Array<{
    capturedAt: string;
    eventType: string;
    changes: Array<{
      field: string;
      oldValue: unknown;
      newValue: unknown;
    }>;
  }>;
}

export interface GeoJsonGeometry {
  type: string;
  coordinates: unknown;
}

@Injectable({ providedIn: 'root' })
export class ApiClient {
  constructor(private readonly http: HttpClient) {}

  systemSummary(): Observable<SystemSummary> {
    return this.http.get<SystemSummary>(`${API_BASE}/system/summary`);
  }

  searchFeeders(filters: { feederId?: string; substationId?: string; minPvThermal?: number; limit?: number; offset?: number }) {
    let params = new HttpParams()
      .set('limit', String(filters.limit ?? 25))
      .set('offset', String(filters.offset ?? 0));
    if (filters.feederId) params = params.set('feederId', filters.feederId);
    if (filters.substationId) params = params.set('substationId', filters.substationId);
    if (filters.minPvThermal !== undefined && filters.minPvThermal !== null) params = params.set('minPvThermal', String(filters.minPvThermal));
    return this.http.get<FeederSearchResponse>(`${API_BASE}/feeders`, { params });
  }

  feeder(feederId: string): Observable<FeederResponse> {
    return this.http.get<FeederResponse>(`${API_BASE}/feeders/${encodeURIComponent(feederId)}`);
  }

  queue(feederId: string): Observable<QueueResponse> {
    return this.http.get<QueueResponse>(`${API_BASE}/feeders/${encodeURIComponent(feederId)}/queue`);
  }

  feederHistory(feederId: string): Observable<FeederHistoryResponse> {
    return this.http.get<FeederHistoryResponse>(`${API_BASE}/feeders/${encodeURIComponent(feederId)}/history`);
  }

  feederChanges(feederId: string): Observable<FeederChangesResponse> {
    return this.http.get<FeederChangesResponse>(`${API_BASE}/feeders/${encodeURIComponent(feederId)}/changes`);
  }

  substation(substationId: string): Observable<SubstationResponse> {
    return this.http.get<SubstationResponse>(`${API_BASE}/substations/${encodeURIComponent(substationId)}`);
  }

  substationFeeders(substationId: string, limit = 50, offset = 0): Observable<FeederSearchResponse> {
    const params = new HttpParams().set('limit', String(limit)).set('offset', String(offset));
    return this.http.get<FeederSearchResponse>(`${API_BASE}/substations/${encodeURIComponent(substationId)}/feeders`, { params });
  }
}
