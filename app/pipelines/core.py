from typing import Iterable, Any, Dict
import logging

logger = logging.getLogger(__name__)


class Pipeline:
    def __init__(self, name: str):
        self.name = name

    def extract(self) -> Iterable[Any]:
        raise NotImplementedError()

    def validate(self, record: Any) -> bool:
        return True

    def transform(self, record: Any) -> Dict[str, Any]:
        raise NotImplementedError()

    def load(self, records: Iterable[Dict[str, Any]]):
        raise NotImplementedError()

    def run(self):
        logger.info("Starting pipeline %s", self.name)
        extracted = []
        for r in self.extract():
            extracted.append(r)

        valid = []
        for r in extracted:
            try:
                if self.validate(r):
                    valid.append(self.transform(r))
            except Exception:
                logger.exception("Validation failed for record")

        self.load(valid)
