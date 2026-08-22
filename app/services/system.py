from app.api.v1.schemas import (
    IngestionRunSummary,
    SourceCapability,
    SystemCounts,
    SystemSources,
    SystemSummaryResponse,
)
from app.config.settings import settings
from app.models import IngestionRun
from app.repositories.system import SystemRepository
from app.services.feeders import QUEUE_UNAVAILABLE_REASON


class SystemSummaryService:
    def __init__(self, repository: SystemRepository):
        self.repository = repository

    def summary(self) -> SystemSummaryResponse:
        counts = self.repository.counts()
        runs = self.repository.latest_ingestions()
        conedison_runs = [run for run in runs if run.pipeline == "conedison_arcgis"]
        latest_conedison = conedison_runs[0] if conedison_runs else None
        mode = _mode_from_run(latest_conedison)

        return SystemSummaryResponse(
            mode=mode,
            environment=settings.app_env,
            counts=SystemCounts(
                feeders=counts.feeders,
                activeFeeders=counts.active_feeders,
                substations=counts.substations,
                feederSnapshots=counts.feeder_snapshots,
                substationSnapshots=counts.substation_snapshots,
                osmSubstations=counts.osm_substations,
                acceptedOsmMatches=counts.accepted_osm_matches,
            ),
            latestIngestions=[_run_summary(run) for run in runs],
            sources=SystemSources(
                conedison=SourceCapability(
                    available=latest_conedison is not None and latest_conedison.status in {"SUCCESS", "UNCHANGED"},
                    note="Con Edison ArcGIS FeatureServer is normalized into customer feeder and substation records.",
                ),
                osm=SourceCapability(
                    available=counts.osm_substations > 0,
                    note="OpenStreetMap substations enrich missing substation geometry when a confident match is found.",
                ),
                queue=SourceCapability(
                    available=False,
                    note=QUEUE_UNAVAILABLE_REASON,
                ),
            ),
            pipelineStages=["extract", "validate", "transform", "load", "snapshot", "serve"],
        )


def _run_summary(run: IngestionRun) -> IngestionRunSummary:
    return IngestionRunSummary(
        id=run.id,
        pipeline=run.pipeline,
        source=run.source,
        status=run.status,
        extractedCount=run.extracted_count or 0,
        validCount=run.valid_count or 0,
        loadedCount=run.loaded_count or 0,
        rejectedCount=run.rejected_count or 0,
        snapshotCreated=bool(run.snapshot_created),
        datasetHashPrefix=run.dataset_hash[:12] if run.dataset_hash else None,
        completedAt=run.completed_at,
        metadata=run.metadata_json or {},
    )


def _mode_from_run(run: IngestionRun | None) -> str:
    if run is None:
        return "empty"
    if run.source == "demo-conedison":
        return "demo"
    if run.source.startswith("http"):
        return "live"
    return "custom"
