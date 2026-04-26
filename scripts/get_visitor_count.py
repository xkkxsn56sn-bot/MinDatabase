#!/usr/bin/env python3
"""Fetch the current visitor count from CountAPI."""

from __future__ import annotations

import argparse
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Read visitor count from CountAPI.')
    parser.add_argument('--namespace', default='medievalvisions-com', help='Counter namespace')
    parser.add_argument('--key', default='site-visits', help='Counter key')
    return parser.parse_args()


def fetch_count(namespace: str, key: str) -> int:
    url = f'https://api.countapi.xyz/get/{namespace}/{key}'
    with urlopen(url, timeout=10) as response:  # nosec B310
        payload = json.loads(response.read().decode('utf-8'))
    if 'value' not in payload:
        raise ValueError(f'Unexpected response: {payload}')
    return int(payload['value'])


def main() -> int:
    args = parse_args()
    try:
        count = fetch_count(args.namespace, args.key)
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        print(f'Error while fetching visitor count: {exc}', file=sys.stderr)
        return 1

    print(f'Visitor count ({args.namespace}/{args.key}): {count}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
