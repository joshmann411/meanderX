import logging
import sys

from app.conedison.client import ConEdisonArcGISClient
from app.pipelines.conedison.pipeline import ConEdisonPipeline

logger = logging.getLogger(__name__)


def main(argv=None):
    argv = argv or sys.argv[1:]
    if len(argv) >= 2 and argv[0] == "ingest" and argv[1] == "conedison":
        client = ConEdisonArcGISClient()
        pipeline = ConEdisonPipeline(client)
        pipeline.run()
        print("Ingestion completed")
    else:
        print("Usage: python -m app.cli ingest conedison")


if __name__ == "__main__":
    main()
