"""
Metrics store: append-only JSON file per run.
Used by CI/CD to assert quality thresholds.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


class MetricsStore:
    """
    Write machine-readable metrics to a JSON file.
    Creates one file per run, named metrics/run_<run_id>.json.
    """

    def __init__(self, run_id: str, metrics_dir: str = "metrics"):
        self.run_id      = run_id
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        self.file_path   = self.metrics_dir / f"run_{run_id}.json"
        self._data: Dict[str, Any] = {
            "run_id":    run_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics":   {},
        }

    def log(self, key: str, value: Any) -> None:
        """Log a single metric value."""
        self._data["metrics"][key] = value
        logger.debug("Metric logged: %s = %s", key, value)

    def log_dict(self, d: Dict[str, Any]) -> None:
        """Log multiple metrics from a dictionary."""
        for k, v in d.items():
            self.log(k, v)

    def save(self) -> str:
        """Write all metrics to disk. Returns file path."""
        with open(self.file_path, "w") as f:
            json.dump(self._data, f, indent=2, default=str)
        logger.info("Metrics saved → %s", self.file_path)
        return str(self.file_path)

    def get(self, key: str, default: Any = None) -> Any:
        return self._data["metrics"].get(key, default)
