import json
from datetime import datetime
from typing import Optional

from app.api.v1.schemas import (
    FeederChangeEvent,
    FeederChangesResponse,
    FeederHistoryEntry,
    FeederHistoryResponse,
    FieldChange,
)
from app.repositories.history import FeederSnapshotRow, HistoryRepository
from app.services.feeders import NotFoundError


class FeederHistoryService:
    def __init__(self, repository: HistoryRepository):
        self.repository = repository

    def get_history(
        self,
        feeder_id: str,
        captured_from: Optional[datetime] = None,
        captured_to: Optional[datetime] = None,
    ) -> FeederHistoryResponse:
        rows = self.repository.feeder_history(feeder_id, captured_from, captured_to)
        if not rows:
            raise NotFoundError("feeder history", feeder_id)
        return FeederHistoryResponse(
            feederId=feeder_id,
            history=[_history_entry(row) for row in rows],
        )

    def get_changes(self, feeder_id: str) -> FeederChangesResponse:
        runs = self.repository.snapshot_runs()
        events = []
        previous = None
        ever_seen = False

        for run in runs:
            current = self.repository.feeder_snapshot_for_run(feeder_id, run.id)
            if previous is None and current is None:
                continue
            if previous is None and current is not None:
                ever_seen = True
                events.append(
                    FeederChangeEvent(
                        capturedAt=current.snapshot.captured_at,
                        eventType="added",
                        changes=[FieldChange(field="feeder", oldValue=None, newValue="present")],
                    )
                )
            elif previous is not None and current is None:
                events.append(
                    FeederChangeEvent(
                        capturedAt=run.started_at,
                        eventType="removed",
                        changes=[FieldChange(field="feeder", oldValue="present", newValue=None)],
                    )
                )
            elif previous is not None and current is not None:
                changes = _compare(previous, current)
                event_type = "modified" if changes else "unchanged"
                events.append(
                    FeederChangeEvent(
                        capturedAt=current.snapshot.captured_at,
                        eventType=event_type,
                        changes=changes,
                    )
                )

            previous = current

        if not ever_seen and not events:
            raise NotFoundError("feeder history", feeder_id)
        return FeederChangesResponse(feederId=feeder_id, changes=events)


def _history_entry(row: FeederSnapshotRow) -> FeederHistoryEntry:
    snapshot = row.snapshot
    return FeederHistoryEntry(
        capturedAt=snapshot.captured_at,
        pvThermal=_capacity_value(snapshot.pv_thermal),
        substationId=snapshot.substation_id,
        geometry=_geojson(row.geometry_geojson),
    )


def _compare(previous: FeederSnapshotRow, current: FeederSnapshotRow) -> list[FieldChange]:
    fields = [
        ("pvThermal", _capacity_value(previous.snapshot.pv_thermal), _capacity_value(current.snapshot.pv_thermal)),
        ("substationId", previous.snapshot.substation_id, current.snapshot.substation_id),
        ("geometry", _geojson(previous.geometry_geojson), _geojson(current.geometry_geojson)),
    ]
    return [
        FieldChange(field=field, oldValue=old_value, newValue=new_value)
        for field, old_value, new_value in fields
        if old_value != new_value
    ]


def _geojson(value: Optional[str]) -> Optional[dict]:
    if not value:
        return None
    return json.loads(value)


def _capacity_value(value: Optional[str]) -> Optional[float | str]:
    if value is None:
        return None
    try:
        return float(str(value).replace(",", "").strip())
    except ValueError:
        return value
