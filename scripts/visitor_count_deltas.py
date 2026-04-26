#!/usr/bin/env python3
"""Print weekly/monthly visitor deltas from CountAPI using local snapshots.

This script stores local historical snapshots so it can calculate deltas over
time from the same counter used by the website tracker.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


DEFAULT_NAMESPACE = "medievalvisions-com"
DEFAULT_KEY = "site-visits"
DEFAULT_HISTORY_PATH = Path("scripts/.visitor_count_history.json")


@dataclass
class Snapshot:
    timestamp: datetime
    count: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Show current visitor count and weekly/monthly deltas."
    )
    parser.add_argument("--namespace", default=DEFAULT_NAMESPACE, help="Counter namespace")
    parser.add_argument("--key", default=DEFAULT_KEY, help="Counter key")
    parser.add_argument(
        "--history-file",
        default=str(DEFAULT_HISTORY_PATH),
        help="Path to local history JSON file",
    )
    return parser.parse_args()


def fetch_count(namespace: str, key: str) -> int:
    url = f"https://api.countapi.xyz/get/{namespace}/{key}"
    with urlopen(url, timeout=10) as response:  # nosec B310
        payload = json.loads(response.read().decode("utf-8"))

    if "value" not in payload:
        raise ValueError(f"Unexpected response: {payload}")

    return int(payload["value"])


def parse_iso_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def load_history(path: Path) -> list[Snapshot]:
    if not path.exists():
        return []

    raw = json.loads(path.read_text(encoding="utf-8"))
    snapshots: list[Snapshot] = []
    for item in raw:
        if "timestamp" not in item or "count" not in item:
            continue
        snapshots.append(
            Snapshot(
                timestamp=parse_iso_datetime(str(item["timestamp"])),
                count=int(item["count"]),
            )
        )

    snapshots.sort(key=lambda snap: snap.timestamp)
    return snapshots


def save_history(path: Path, snapshots: list[Snapshot]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serializable = [
        {
            "timestamp": snap.timestamp.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "count": snap.count,
        }
        for snap in snapshots
    ]
    path.write_text(json.dumps(serializable, indent=2), encoding="utf-8")


def append_snapshot(history: list[Snapshot], snapshot: Snapshot) -> list[Snapshot]:
    history.append(snapshot)

    deduped: list[Snapshot] = []
    for snap in sorted(history, key=lambda item: item.timestamp):
        if deduped and deduped[-1].timestamp == snap.timestamp:
            deduped[-1] = snap
        else:
            deduped.append(snap)
    return deduped


def delta_for_period(history: list[Snapshot], now: datetime, current_count: int, days: int) -> int | None:
    target_time = now - timedelta(days=days)
    candidates = [snap for snap in history if snap.timestamp <= target_time]
    if not candidates:
        return None

    baseline = max(candidates, key=lambda snap: snap.timestamp)
    return current_count - baseline.count


def print_delta(label: str, delta: int | None) -> None:
    if delta is None:
        print(f"{label}: n/a (need older snapshot)")
        return

    sign = "+" if delta >= 0 else ""
    print(f"{label}: {sign}{delta}")


def main() -> int:
    args = parse_args()
    history_path = Path(args.history_file)

    try:
        current_count = fetch_count(args.namespace, args.key)
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        print(f"Error while fetching visitor count: {exc}", file=sys.stderr)
        return 1

    now = datetime.now(timezone.utc)
    history = load_history(history_path)
    history = append_snapshot(history, Snapshot(timestamp=now, count=current_count))
    save_history(history_path, history)

    weekly_delta = delta_for_period(history, now, current_count, days=7)
    monthly_delta = delta_for_period(history, now, current_count, days=30)

    print(f"Counter: {args.namespace}/{args.key}")
    print(f"Current visitors (page views): {current_count}")
    print_delta("Last 7 days", weekly_delta)
    print_delta("Last 30 days", monthly_delta)
    print(f"Snapshots stored in: {history_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
