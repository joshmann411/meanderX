import logging
import sys

import uvicorn

from app.conedison.client import ConEdisonArcGISClient
from app.demo import seed_demo_data
from app.pipelines.conedison.pipeline import ConEdisonPipeline
from app.pipelines.osm.client import OsmOverpassClient
from app.pipelines.osm.pipeline import OsmSubstationPipeline

logger = logging.getLogger(__name__)


def main(argv=None):
    argv = argv or sys.argv[1:]
    if len(argv) >= 2 and argv[0] == "ingest" and argv[1] == "conedison":
        ConEdisonPipeline(ConEdisonArcGISClient()).run()
        print("Con Edison ingestion completed")
    elif len(argv) >= 2 and argv[0] == "ingest" and argv[1] == "osm":
        OsmSubstationPipeline(OsmOverpassClient()).run()
        print("OSM substation ingestion completed")
    elif len(argv) >= 2 and argv[0] == "ingest" and argv[1] == "all":
        ConEdisonPipeline(ConEdisonArcGISClient()).run()
        OsmSubstationPipeline(OsmOverpassClient()).run()
        print("All ingestion completed")
    elif len(argv) >= 2 and argv[0] == "demo" and argv[1] == "seed":
        seed_demo_data()
    elif len(argv) >= 1 and argv[0] == "api":
        uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
    elif len(argv) >= 1 and argv[0] in {"help", "--help", "-h"}:
        print(_help_text())
    else:
        print(_help_text())
        raise SystemExit(2)


def _help_text() -> str:
    return """Usage:
  python -m app.cli ingest conedison
  python -m app.cli ingest osm
  python -m app.cli ingest all
  python -m app.cli demo seed
  python -m app.cli api"""


if __name__ == "__main__":
    main()
