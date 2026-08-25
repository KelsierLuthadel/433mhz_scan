"""Optional file/JSONL output for decoded packets."""

import json
from pathlib import Path

from .packet import DecodedPacket


class JsonlLogger:
    """Append one JSON line per packet to a .jsonl file."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self.path.open("a", encoding="utf-8")

    def log(self, pkt: DecodedPacket) -> None:
        record = {"_logged": pkt.time.isoformat()} | pkt.raw
        self._file.write(json.dumps(record) + "\n")
        self._file.flush()

    def close(self) -> None:
        self._file.close()

    def __enter__(self) -> "JsonlLogger":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
