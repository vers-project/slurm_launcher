"""
Job timing utility.

Records start/end timestamps and wall-clock duration to timing.json in the
job output directory.  Works identically for local and SLURM execution.

SLURM timeout handling
----------------------
When a SLURM job exceeds its allocated time, SLURM sends SIGTERM to the
running processes.  JobTimer installs a SIGTERM handler that writes the timing
file with status "interrupted" before allowing the process to exit, so the
file is always written even if the job never reaches its natural end.

timing.json schema
------------------
{
  "start":            "2026-07-03T14:22:10.123456+00:00",
  "end":              "2026-07-03T16:45:33.456789+00:00",
  "duration_seconds": 8603.333,
  "status":           "completed" | "interrupted" | "failed"
}

  completed   — function returned normally
  interrupted — SIGTERM received (SLURM timeout, scancel) or KeyboardInterrupt
  failed      — unhandled exception raised inside the job
"""

from __future__ import annotations

import json
import os
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path


class JobTimer:
    """
    Context manager that writes timing.json to *output_dir*.

    Usage::

        with JobTimer(output_dir):
            run_experiment(...)
    """

    FILENAME = "timing.json"

    def __init__(self, output_dir: Path) -> None:
        self._path = Path(output_dir) / self.FILENAME
        self._start: datetime | None = None
        self._finalized = False
        self._prev_sigterm: signal.Handlers | None = None

    # ------------------------------------------------------------------
    # Context manager protocol
    # ------------------------------------------------------------------

    def __enter__(self) -> "JobTimer":
        self._start = datetime.now(timezone.utc)
        self._write("running", end=None)
        self._prev_sigterm = signal.signal(signal.SIGTERM, self._handle_sigterm)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if self._prev_sigterm is not None:
            signal.signal(signal.SIGTERM, self._prev_sigterm)

        if self._finalized:
            # SIGTERM handler already wrote the file — don't overwrite
            return False

        if exc_type is None:
            self._finalize("completed")
        elif exc_type in (SystemExit, KeyboardInterrupt):
            self._finalize("interrupted")
        else:
            self._finalize("failed")

        return False  # never suppress exceptions

    # ------------------------------------------------------------------
    # SIGTERM handler (invoked by SLURM on timeout / scancel)
    # ------------------------------------------------------------------

    def _handle_sigterm(self, signum: int, frame) -> None:
        self._finalize("interrupted")
        # Restore default handler and re-raise SIGTERM so the process exits
        # with the correct signal code (important for SLURM accounting).
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        os.kill(os.getpid(), signal.SIGTERM)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _finalize(self, status: str) -> None:
        self._finalized = True
        self._write(status)

    def _write(self, status: str, end: datetime | None = ...) -> None:  # type: ignore[assignment]
        now = datetime.now(timezone.utc)
        if end is ...:
            end = now

        data: dict = {"start": self._start.isoformat() if self._start else None}

        if end is not None:
            data["end"] = end.isoformat()
            if self._start is not None:
                data["duration_seconds"] = round((end - self._start).total_seconds(), 3)
        else:
            data["end"] = None
            data["duration_seconds"] = None

        data["status"] = status

        try:
            self._path.write_text(json.dumps(data, indent=2) + "\n")
        except OSError as exc:
            print(f"[JobTimer] WARNING: could not write {self._path}: {exc}", file=sys.stderr)
