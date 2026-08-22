import { Component, Input } from '@angular/core';
import { GeoJsonGeometry } from '../api-client';

type Point = [number, number];

@Component({
  selector: 'app-geometry-preview',
  templateUrl: './geometry-preview.html',
  styleUrl: './geometry-preview.scss'
})
export class GeometryPreview {
  @Input() geometry?: GeoJsonGeometry | null;

  get points(): Point[] {
    return flattenCoordinates(this.geometry?.coordinates);
  }

  get path(): string {
    const projected = this.projectedPoints;
    if (!projected.length) return '';
    return projected.map((point, index) => `${index === 0 ? 'M' : 'L'} ${point[0]} ${point[1]}`).join(' ');
  }

  get projectedPoints(): Point[] {
    const points = this.points;
    if (!points.length) return [];

    const xs = points.map((point) => point[0]);
    const ys = points.map((point) => point[1]);
    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);
    const spanX = Math.max(maxX - minX, 0.000001);
    const spanY = Math.max(maxY - minY, 0.000001);

    return points.map(([x, y]) => [
      24 + ((x - minX) / spanX) * 252,
      156 - ((y - minY) / spanY) * 132,
    ]);
  }
}

function flattenCoordinates(value: unknown): Point[] {
  if (!Array.isArray(value)) return [];
  if (value.length >= 2 && typeof value[0] === 'number' && typeof value[1] === 'number') {
    return [[value[0], value[1]]];
  }
  return value.flatMap((item) => flattenCoordinates(item));
}
