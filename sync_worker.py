"""6-hour Google Blogger/YouTube sync worker (V2 zip parity).

  python sync_worker.py --once
  python sync_worker.py --loop
"""
from __future__ import annotations

import argparse
import time

import app
import integrations_v2

INTERVAL = integrations_v2.SYNC_INTERVAL_SEC


def sync_once(*, force: bool = False):
    app.init_db()
    with app.connect() as db:
        with app.transaction(db):
            return integrations_v2.run_scheduled_syncs(db, force=force)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--loop', action='store_true')
    parser.add_argument('--once', action='store_true')
    parser.add_argument('--force', action='store_true', help='Ignore 6h interval')
    args = parser.parse_args()
    while True:
        print('LAWYGO Google sync', sync_once(force=args.force), flush=True)
        if not args.loop:
            break
        time.sleep(INTERVAL)
