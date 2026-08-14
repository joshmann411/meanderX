import logging
import re
from datetime import datetime, timezone
from difflib import SequenceMatcher
from statistics import median
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.models import Feeder, OsmSubstation, Substation, SubstationOsmMatch

logger = logging.getLogger(__name__)


class SubstationMatcher:
    def __init__(self, db: Session, threshold: Optional[float] = None):
        self.db = db
        self.threshold = settings.osm_match_threshold if threshold is None else threshold

    def match_all(self, run_id: Optional[int] = None) -> dict:
        substations = self.db.query(Substation).all()
        osm_substations = self.db.query(OsmSubstation).all()
        evaluated = 0
        accepted = 0
        low_confidence = 0
        unresolved = 0
        scores = []

        for substation in substations:
            candidates = [self.score(substation, osm) for osm in osm_substations]
            candidates = [candidate for candidate in candidates if candidate is not None]
            evaluated += len(candidates)
            if not candidates:
                unresolved += 1
                continue
            candidates.sort(key=lambda item: item["confidence"], reverse=True)
            best = candidates[0]
            second = candidates[1] if len(candidates) > 1 else None
            ambiguous = second is not None and best["confidence"] - second["confidence"] < 0.05
            is_accepted = best["confidence"] >= self.threshold and not ambiguous
            if is_accepted:
                accepted += 1
            else:
                low_confidence += 1

            scores.append(best["confidence"])
            self._store_match(substation, best, run_id, is_accepted)

        summary = {
            "osmSubstations": len(osm_substations),
            "substations": len(substations),
            "candidatesEvaluated": evaluated,
            "accepted": accepted,
            "lowConfidence": low_confidence,
            "unresolved": unresolved,
            "averageConfidence": round(sum(scores) / len(scores), 4) if scores else None,
            "medianConfidence": round(median(scores), 4) if scores else None,
        }
        logger.info("OSM matching summary: %s", summary)
        return summary

    def score(self, substation: Substation, osm_substation: OsmSubstation) -> Optional[dict]:
        sub_name = substation.name or substation.source_substation_id
        name_score = name_similarity(sub_name, osm_substation.name)
        operator_score = _operator_score(osm_substation.operator)
        distance_meters = self._distance_to_feeder_centroid(substation.id, osm_substation.id)
        distance_score = _distance_score(distance_meters)

        if distance_meters is None:
            confidence = min(1.0, name_score * 0.85 + operator_score * 0.15)
            method = "name_operator"
        else:
            confidence = min(1.0, name_score * 0.65 + operator_score * 0.15 + distance_score * 0.20)
            method = "name_operator_proximity"

        if confidence <= 0:
            return None
        return {
            "osm_substation": osm_substation,
            "confidence": round(confidence, 4),
            "match_method": method,
            "distance_meters": round(distance_meters, 2) if distance_meters is not None else None,
        }

    def _store_match(self, substation: Substation, candidate: dict, run_id: Optional[int], accepted: bool) -> None:
        existing = (
            self.db.query(SubstationOsmMatch)
            .filter_by(substation_id=substation.id, osm_substation_id=candidate["osm_substation"].id)
            .one_or_none()
        )
        if existing is None:
            existing = SubstationOsmMatch(
                substation_id=substation.id,
                osm_substation_id=candidate["osm_substation"].id,
            )
            self.db.add(existing)
        existing.ingestion_run_id = run_id
        existing.confidence = candidate["confidence"]
        existing.match_method = candidate["match_method"]
        existing.distance_meters = candidate["distance_meters"]
        existing.accepted = accepted
        existing.matched_at = datetime.now(timezone.utc)

    def _distance_to_feeder_centroid(self, substation_id: int, osm_substation_id: int) -> Optional[float]:
        feeder_centroid = func.ST_Centroid(func.ST_Collect(Feeder.geometry))
        row = (
            self.db.query(func.ST_DistanceSphere(feeder_centroid, OsmSubstation.centroid))
            .select_from(Feeder)
            .join(OsmSubstation, OsmSubstation.id == osm_substation_id)
            .filter(Feeder.substation_id == substation_id, Feeder.geometry.isnot(None))
            .group_by(OsmSubstation.centroid)
            .first()
        )
        if not row:
            return None
        return float(row[0]) if row[0] is not None else None


def name_similarity(left: Optional[str], right: Optional[str]) -> float:
    left_norm = normalize_name(left)
    right_norm = normalize_name(right)
    if not left_norm or not right_norm:
        return 0.0
    if left_norm == right_norm:
        return 1.0
    if left_norm in right_norm or right_norm in left_norm:
        return 0.9
    return SequenceMatcher(None, left_norm, right_norm).ratio()


def normalize_name(value: Optional[str]) -> str:
    if not value:
        return ""
    value = value.lower()
    value = re.sub(r"\b(substation|station|sub|yard|switching)\b", " ", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def _operator_score(operator: Optional[str]) -> float:
    normalized = normalize_name(operator)
    if not normalized:
        return 0.0
    if "consolidated edison" in normalized or "con edison" in normalized or "conedison" in normalized:
        return 1.0
    if "edison" in normalized:
        return 0.6
    return 0.0


def _distance_score(distance_meters: Optional[float]) -> float:
    if distance_meters is None:
        return 0.0
    if distance_meters <= 250:
        return 1.0
    if distance_meters >= 3000:
        return 0.0
    return max(0.0, 1 - ((distance_meters - 250) / 2750))
